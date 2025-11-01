from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
from socket import *
from pydantic import BaseModel
from shared.config import NAMENODE_HOST, NAMENODE_PORT, DATANODES
import hashlib
from typing import List, Dict

app = FastAPI()
CHUNK_SIZE = 2 * 1024 * 1024

class UploadResponse(BaseModel):
    filename: str
    file_size: int
    chunks_processed: int
    file_hash: str
    message: str


def request_chunk_write(filename, num_chunks):
    namenode_port = NAMENODE_PORT
    namenode_host = NAMENODE_HOST

    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((namenode_host, namenode_port))
        
        req = {
            "type": "write_req",
            "filename": filename,
            "num_chunks": num_chunks
        }

        sock.send(json.dumps(req).encode())
        data = sock.recv(4096)
        chunk_placements = json.loads(data.decode())
        sock.close()
        return chunk_placements
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error contacting namenode: {str(e)}")


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


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    total_size = 0
    chunk_count = 0
    file_hash = hashlib.md5()
    
    try:
        while True:
            chunk_data = await file.read(CHUNK_SIZE)
            if not chunk_data:
                break
            
            total_size += len(chunk_data)
            file_hash.update(chunk_data)
            
            chunk_placements = request_chunk_write(file.filename, chunk_count + 1)
            
            if not chunk_placements:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to get chunk placement from namenode"
                )
            
            if str(chunk_count) not in chunk_placements:
                raise HTTPException(
                    status_code=500,
                    detail=f"No placement info for chunk {chunk_count}"
                )
            
            assigned_datanodes = chunk_placements[str(chunk_count)]
            stored_successfully = False

            for datanode_id in assigned_datanodes:
                datanode_info = next(
                    (dn for dn in DATANODES if dn['id'] == datanode_id), 
                    None
                )
                
                if not datanode_info:
                    continue
                
                success = send_chunk_to_datanode(
                    chunk_data, 
                    datanode_info, 
                    chunk_count, 
                    file.filename
                )
                
                if success:
                    stored_successfully = True
            
            if not stored_successfully:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to store chunk {chunk_count} on any datanode"
                )
            
            chunk_count += 1
        
        if chunk_count == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        final_hash = file_hash.hexdigest()
        
        return UploadResponse(
            filename=file.filename,
            file_size=total_size,
            chunks_processed=chunk_count,
            file_hash=final_hash,
            message=f"File uploaded successfully in {chunk_count} chunks"
        )
    
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)