from fastapi import FastAPI
import json
from socket import *
from pydantic import BaseModel
from shared.config import NAMENODE_HOST, NAMENODE_PORT

app = FastAPI()

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
        print(f"Some error: {e}")

