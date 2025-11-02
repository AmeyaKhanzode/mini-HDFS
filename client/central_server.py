from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import logging
import math
from fastapi.responses import JSONResponse
import json
from socket import *
from pydantic import BaseModel
from shared.config import NAMENODE_HOST, NAMENODE_PORT, DATANODES, CHUNK_SIZE
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
        reader, writer = await asyncio.open_connection(NAMENODE_HOST, NAMENODE_PORT)

        req = {
            "type": "write_req",
            "filename": filename,
            "num_chunks": num_chunks
        }

        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()

        data = await reader.readline()
        writer.close()
        await writer.wait_closed()

        return json.loads(data.decode().strip())
    except Exception as e:
        logger.error(f"Failed to get chunk placements from namenode: {e}")
        return None


# TODO check for ACK only then send


def send_chunk_to_datanode(chunk_data, datanode_info, chunk_index, file_id, chunk_hash, max_retries=3):
    for attempt in range(max_retries):
        sock = None
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((datanode_info['host'], datanode_info['port']))
            
            metadata = {
                "type": "write_chunk",
                "file_id": file_id,
                "chunk_index": chunk_index,
                "chunk_hash": chunk_hash
            }
            
            sock.send(json.dumps(metadata).encode())

            # to get an ACK
            ack = sock.recv(4096)
            if not ack:
                raise Exception("No ACK from datanode")

            #send data only after an ACK
            sock.sendall(chunk_data)
            response = sock.recv(1024)
            sock.close()
            return True
        
        except Exception as e:
            if sock:
                sock.close()
                logger.warning(f"Retry {attempt+1}/{max_retries} for chunk {chunk_index} to {datanode_info['host']}:{datanode_info['port']} ({e})")
            if attempt == max_retries - 1:
                return False
            continue
    
    return False


# TODO await asyncio.gather(*upload_tasks), wanna implement this later

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_size: int = Form(...)
):

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    chunk_count = math.ceil(file_size / CHUNK_SIZE)
    
    placement_response = await request_chunk_write(file.filename, chunk_count)
    if not placement_response or "placements" not in placement_response:
            raise HTTPException(status_code=500, detail="Failed to get chunk placements from Namenode")

    file_id = placement_response["file_id"]
    chunk_placements = placement_response["placements"]

    try:
        chunk_index = 0
        while True:
            chunk_data = await file.read(CHUNK_SIZE)
            if not chunk_data:
                break
            

            chunk_index += 1
            chunk_id = f"chunk_{chunk_index}"
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()

            if chunk_id not in chunk_placements:
                raise HTTPException(status_code=500, detail=f"No placement info for {chunk_id}")

            datanodes = chunk_placements[chunk_id]

            for node in datanodes:
                host, port = node.split(":")

                datanode_info = {
                    "host": host,
                    "port": int(port),
                }

                ok = send_chunk_to_datanode(chunk_data, datanode_info, chunk_index, file_id, chunk_hash) 
                if not ok:
                    raise HTTPException(status_code=500, detail=f"Failed to send chunk {chunk_index} to {host}:{port}")
        
        return UploadResponse(
            filename=file.filename,
            file_size=file_size,
            num_chunks=chunk_count,
            file_id=file_id,
            message="File uploaded successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )
    
    finally:
        await file.close()


@app.get("/")
async def root():
    return {
        "message": "Mini-HDFS Client API", 
        "status": "running",
        "chunk_size": f"{CHUNK_SIZE / (1024 * 1024)}MB",
        "namenode": f"{NAMENODE_HOST}:{NAMENODE_PORT}"
    }


@app.get("/config")
async def get_config():
    return {
        "namenode": {
            "host": NAMENODE_HOST,
            "port": NAMENODE_PORT
        },
        "datanodes": DATANODES,
        "chunk_size_mb": CHUNK_SIZE / (1024 * 1024)
    }