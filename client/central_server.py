from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import logging
import math
from fastapi.responses import JSONResponse
import json
from socket import *
from pydantic import BaseModel
from shared.config import NAMENODE_HOST, NAMENODE_PORT, DATANODES
import hashlib
from typing import List, Dict
import asyncio

app = FastAPI()
CHUNK_SIZE = 2 * 1024 * 1024

class UploadResponse(BaseModel):
    filename: str
    file_size: int
    chunks_processed: int
    file_hash: str
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
        print(f"Some shit went wrong {e}")


def send_chunk_to_datanode(chunk_data: bytes, datanode_info: Dict, chunk_id: int, filename: str, max_retries: int = 3):
    for attempt in range(max_retries):
        sock = None
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((datanode_info['host'], datanode_info['port']))
            
            metadata = {
                "type": "write_chunk",
                "filename": filename,
                "chunk_id": chunk_id,
                "chunk_size": len(chunk_data)
            }
            
            sock.send(json.dumps(metadata).encode())
            sock.recv(1024)
            sock.sendall(chunk_data)
            response = sock.recv(1024)
            sock.close()
            
            return True
        
        except Exception as e:
            if sock:
                sock.close()
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
    chunk_count = math.ceil(file_size / CHUNK_SIZE)
    chunk_placements = await request_chunk_write(file.filename, chunk_count)

    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    file_hash = hashlib.sha256()
    
    try:
        chunk_index = 0
        while True:
            chunk_data = await file.read(CHUNK_SIZE)
            if not chunk_data:
                break
            
            file_hash.update(chunk_data)
            
            if not chunk_placements:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to get chunk placement from namenode"
                )
            
            chunk_index += 1
            chunk_id = f"chunk_{chunk_index}"

            if chunk_id not in chunk_placements:
                raise HTTPException(status_code=500, detail=f"No placement info for {chunk_id}")

            nodes = chunk_placements[chunk_id]

            for i in nodes:
                host, port = i.split(":")

                datanode_info = {
                    "host": host,
                    "port": int(port),
                }

                if send_chunk_to_datanode(chunk_data, datanode_info, chunk_id, file.filename):
                    continue
                else:
                    print("lalith put raise here")
        
        final_hash = file_hash.hexdigest()
        
        return {
            "filename": file.filename,
            "num_chunks": chunk_count,
            "file_hash": final_hash,
            "message": f"File uploaded successfully"
        }

    except HTTPException:
        raise
    
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