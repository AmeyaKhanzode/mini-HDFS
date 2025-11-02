from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import logging
import math
from fastapi.responses import JSONResponse
import json
from socket import *
from pydantic import BaseModel
from shared.config import NAMENODE_HOST, NAMENODE_REQ_PORT, DATANODES, CHUNK_SIZE
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


# TODO check for ACK only then send


def send_chunk_to_datanode(chunk_data, datanodes, chunk_index, file_id, chunk_hash):
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
            return True
        else:
            logger.error(f"Unexpected response from {primary}: {response}")
            return False
    except Exception as e:
        logger.error(f"Failed to send chunk {chunk_index} to {primary}: {e}")
        return False
    finally:
        sock.close()


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

    try:
        chunk_index = 0
        while True:
            chunk_data = await file.read(CHUNK_SIZE)
            logger.info(f"some chunk data read {chunk_index + 1}")
            if not chunk_data:
                break
            

            chunk_index += 1
            chunk_id = f"chunk_{chunk_index}"
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()

            if chunk_id not in chunk_placements:
                raise HTTPException(status_code=500, detail=f"No placement info for {chunk_id}")

            datanodes = chunk_placements[chunk_id]
            '''
            now datanodes looks like this
                ["datanode1:5001", "datanode2:5002"]
            '''

            logger.info("sending to datanode")
            ok = send_chunk_to_datanode(chunk_data, datanodes, chunk_index, file_id, chunk_hash) 
            logger.info("sent to datanode")
            if not ok:
                raise HTTPException(status_code=500, detail=f"Failed to send chunk {chunk_index} via pipeline {datanodes}")
        
        return UploadResponse(
            filename=file.filename,
            file_size=file_size,
            num_chunks=chunk_count,
            file_id=file_id,
            message="File uploaded successfully"
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


@app.get("/")
async def root():
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