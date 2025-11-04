from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import logging
import math
from fastapi.responses import JSONResponse
import json
from socket import *
from pydantic import BaseModel
from shared.config import NAMENODE_HOST, NAMENODE_REQ_PORT, DATANODES, CHUNK_SIZE
from shared.commons import *
import hashlib
from typing import List, Dict
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

class UploadResponse(BaseModel):
    filename: str
    file_size: int
    num_chunks: int
    file_id: str
    message: str


async def request_chunk_write(filename, num_chunks):
    try:
        logger.info(f"Connecting to namenode at {NAMENODE_HOST}:{NAMENODE_REQ_PORT}")
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(NAMENODE_HOST, NAMENODE_REQ_PORT),
            timeout=5.0
        )
        logger.info("Connected to namenode")

        req = {
            "type": "write_req",
            "filename": filename,
            "num_chunks": num_chunks
        }

        logger.info(f"Sending request: {req}")
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()

        logger.info("Waiting for response...")
        data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        logger.info(f"Received response: {data}")
        
        writer.close()
        await writer.wait_closed()

        logger.info("Sending info to backend")
        return json.loads(data.decode().strip())
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for namenode response")
        return None
    except Exception as e:
        logger.error(f"Failed to get chunk placements from namenode: {e}")
        return None


async def store_metadata(filename, file_hash, file_size, num_chunks, placements, chunk_hashes):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(NAMENODE_HOST, NAMENODE_REQ_PORT),
            timeout=5.0
        )

        req = {
            "type": "metadata_write",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "num_chunks": num_chunks,
            "placements": placements,
            "chunk_hashes": chunk_hashes
        }

        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()

        data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        response = json.loads(data.decode().strip())
        
        writer.close()
        await writer.wait_closed()
        
        return response.get("status") == "ok"
    except Exception as e:
        logger.error(f"Failed to store metadata on namenode: {e}")
        return False


def send_chunk_to_datanode(filename, chunk_data, datanodes, chunk_index, file_id, chunk_hash):
    primary = datanodes[0]
    downstream = datanodes[1:]
    host, port = primary.split(":")

    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, int(port)))

        metadata = {
            "type": "write_chunk",
            "file_id": file_id,
            "chunk_index": chunk_index,
            "chunk_hash": chunk_hash,
            "downstream": downstream
        }

        logger.info(f"Sending metadata for chunk {chunk_index} → {primary}")
        sock.send(json.dumps(metadata).encode())

        ack = sock.recv(4096)
        if not ack:
            raise Exception("No ACK from datanode")

        sock.sendall(chunk_data)
        sock.shutdown(SHUT_WR)

        response = sock.recv(1024)
        if b"STORED" in response:
            logger.info(f"Chunk {chunk_index} successfully stored via pipeline starting at {primary}")

            # TODO store metadata here

            return True
        else:
            logger.error(f"Unexpected response from {primary}: {response}")
            return False
    except Exception as e:
        logger.error(f"Failed to send chunk {chunk_index} to {primary}: {e}")
        return False
    finally:
        sock.close()

def request_rename(temp_id, file_hash, datanodes):
    """Request all datanodes to rename temp UUID directory to file hash"""
    success_count = 0
    
    for datanode in datanodes:
        try:
            host, port = datanode.split(":")
            sock = socket(AF_INET, SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, int(port)))
            
            metadata = {
                "type": "rename_file",
                "old_id": temp_id,
                "new_id": file_hash
            }
            
            sock.send(json.dumps(metadata).encode())
            response = sock.recv(1024)
            sock.close()
            
            if b"RENAMED" in response:
                logger.info(f"Renamed {temp_id} → {file_hash} on {datanode}")
                success_count += 1
            else:
                logger.error(f"Failed to rename on {datanode}: {response}")
                
        except Exception as e:
            logger.error(f"Error renaming on {datanode}: {e}")
    
    return success_count

def get_chunk_map(filename):

    req = {
        "type": "read_req",
        "subtype": "read_file",
        "filename": filename
    }

    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((NAMENODE_HOST, NAMENODE_REQ_PORT))

        sock.sendall((json.dumps(req) + "\n").encode())

        data = read_till_newline(sock)
        json_data = json.loads(data)
        
        sock.close()
        return json_data
    except Exception as e:
        logger.error(f"Error getting chunk map: {e}")
        return None


# TODO await asyncio.gather(*upload_tasks), wanna implement this later

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_size: int = Form(...)
):
    logger.info(f"Upload request received: filename={file.filename}, size={file_size}")

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    chunk_count = math.ceil(file_size / CHUNK_SIZE)
    logger.info(f"Requesting placement for {chunk_count} chunks")
    
    placement_response = await request_chunk_write(file.filename, chunk_count)
    '''
    placement response should look like this
        {
            "file_id": "b10a2f8a-97a5-4d30-becb-2a76d...",
            "placements": {
                "chunk_1": ["datanode1:5001", "datanode2:5002"],
                "chunk_2": ["datanode2:5002", "datanode1:5001"]
            }
        }
    '''

    logger.info(f"got placement data {placement_response}")
    if not placement_response or "placements" not in placement_response:
            raise HTTPException(status_code=500, detail="Failed to get chunk placements from Namenode")

    file_id = placement_response["file_id"]
    chunk_placements = placement_response["placements"]
    '''
    chunk_placements should look like this
        "placements": 
        {
            "chunk_1": ["datanode1:5001", "datanode2:5002"],
            "chunk_2": ["datanode2:5002", "datanode1:5001"]
        }
    '''

    # Calculate file hash incrementally while uploading chunks
    file_hasher = hashlib.sha256()
    chunk_hashes = []

    try:
        chunk_index = 0
        while True:
            chunk_data = await file.read(CHUNK_SIZE)
            if not chunk_data:
                break
            
            chunk_index += 1
            
            # Update file hash incrementally
            file_hasher.update(chunk_data)
            
            logger.info(f"Processing chunk {chunk_index}/{chunk_count}")
            
            chunk_id = f"chunk_{chunk_index}"
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            chunk_hashes.append(chunk_hash)

            if chunk_id not in chunk_placements:
                raise HTTPException(status_code=500, detail=f"No placement info for {chunk_id}")

            datanodes = chunk_placements[chunk_id]
            '''
            now datanodes looks like this
                ["datanode1:5001", "datanode2:5002"]
            '''

            logger.info("sending to datanode")
            ok = send_chunk_to_datanode(file.filename, chunk_data, datanodes, chunk_index, file_id, chunk_hash) 
            logger.info("sent to datanode")
            if not ok:
                raise HTTPException(status_code=500, detail=f"Failed to send chunk {chunk_index} via pipeline {datanodes}")
        
        # After all chunks uploaded, get final file hash
        file_hash = file_hasher.hexdigest()
        
        # Collect all unique datanodes that received chunks
        all_datanodes = set()
        for chunk_id, nodes in chunk_placements.items():
            all_datanodes.update(nodes)
        
        # Request rename on all datanodes: temp_id → file_hash
        renamed_count = request_rename(file_id, file_hash, all_datanodes)
        
        # Store metadata on namenode
        metadata_stored = await store_metadata(
            filename=file.filename,
            file_hash=file_hash,
            file_size=file_size,
            num_chunks=chunk_count,
            placements=chunk_placements,
            chunk_hashes=chunk_hashes
        )
        
        if not metadata_stored:
            logger.warning("Failed to store metadata on namenode")
        
        return UploadResponse(
            filename=file.filename,
            file_size=file_size,
            num_chunks=chunk_count,
            file_id=file_hash,
            message=f"File uploaded successfully"
        )

    except Exception as e:
        # Log full exception with traceback to help debugging
        logger.exception("Error uploading file")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )
    
    finally:
        if 'sock' in locals():
            await file.close()


@app.get("/api/status")
async def status():
    return {
        "message": "Mini-HDFS Client API", 
        "status": "running",
        "chunk_size": f"{CHUNK_SIZE / (1024 * 1024)}MB",
        "namenode": f"{NAMENODE_HOST}:{NAMENODE_REQ_PORT}"
    }


@app.get("/config")
async def get_config():
    return {
        "namenode": {
            "host": NAMENODE_HOST,
            "port": NAMENODE_REQ_PORT
        },
        "datanodes": DATANODES,
        "chunk_size_mb": CHUNK_SIZE / (1024 * 1024)
    }

@app.get("/list_files")
async def list_files():
    """Get list of all files from namenode using sync socket"""
    try:
        # Use synchronous socket - FastAPI will run this in a thread pool
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((NAMENODE_HOST, NAMENODE_REQ_PORT))
        
        req = {
            "type": "read_req",
            "subtype": "list_files"
        }
        
        # Send request
        sock.sendall((json.dumps(req) + "\n").encode())
        
        # Receive response
        response_data = sock.recv(4096).decode()
        sock.close()
        
        response = json.loads(response_data)
        
        if response.get("status") == "ok":
            return {"files": response.get("files", [])}
        else:
            raise HTTPException(status_code=500, detail=response.get("message", "Failed to fetch files"))
            
    except timeout:
        logger.error("Timeout connecting to namenode")
        raise HTTPException(status_code=503, detail="Namenode unavailable")
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
