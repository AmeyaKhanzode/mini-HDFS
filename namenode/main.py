# For each chunk, requests placement info from Namenode.
import uuid
import threading
import random
from socket import *
import json
import logging
import os
from shared.commons import create_socket
from shared.config import BACKEND_HOST, BACKEND_PORT, NAMENODE_REQ_PORT, REPLICATION_FACTOR
from heartbeat_handler import get_alive_datanodes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def assign_datanodes(num_chunks):
    # algo to assign chunks
    # returns a dict of where to store {chunk1: [], chunk2: []}
    '''
    {
        "file_id": "b10a2f8a-97a5-4d30-becb-2a76d...",
        "placements": {
            "chunk_1": ["datanode1:5001", "datanode2:5002"],
            "chunk_2": ["datanode2:5002", "datanode1:5001"]
        }
    }

    '''
    alive_datanodes = get_alive_datanodes()


    if REPLICATION_FACTOR > len(alive_datanodes):
        logger.warning(f"Not enough datanodes: need {REPLICATION_FACTOR}, got {len(alive_datanodes)}")
        return {
            "error": "not enough datanodes"
        }

    placements = {}

    file_id = str(uuid.uuid4())
    
    random.shuffle(alive_datanodes)

    for i in range(num_chunks):
        selected_nodes = random.sample(alive_datanodes, REPLICATION_FACTOR)

        chunk_id = f"chunk_{i + 1}"
        placements[chunk_id] = [f"{node['host']}:{node['port']}" for node in selected_nodes]
        
    return {
        "file_id": file_id,
        "placements": placements
    }

def handle_client(client_sock, addr):
    logger = logging.getLogger(__name__)
    try:
        data = client_sock.recv(4096)
        if not data:
            return

        req_data = json.loads(data.decode())
        if req_data:
            if req_data.get("type") == "write_req":
                # TODO call function to add metadata to metastore after all the replication and storage is done
                filename = req_data.get("filename")
                num_chunks = req_data.get("num_chunks")

                alive_datanodes = get_alive_datanodes()

                chunk_placements = assign_datanodes(num_chunks)
                client_sock.sendall((json.dumps(chunk_placements) + "\n").encode())
    except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
    finally:
        client_sock.close()

def req_listener():
    logger = logging.getLogger(__name__)
    try:
        sock = create_socket("0.0.0.0", NAMENODE_REQ_PORT)
        sock.listen()
        logger.info(f"Namenode request listener active on port {NAMENODE_REQ_PORT}")

        while True:
            client_sock, addr = sock.accept()
            threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True
            ).start()
    except Exception as e:
        logger.error(f"FATAL: Request listener failed: {e}", exc_info=True)
        raise


            
