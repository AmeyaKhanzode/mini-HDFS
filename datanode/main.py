from socket import *
import threading
import hashlib
import json
import os
import logging
from shared.commons import create_socket
from shared.config import DATANODE_PORT

STORAGE_PATH = os.path.expanduser("/data")
os.makedirs(STORAGE_PATH, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_chunk(file_id, chunk_index, chunk_data, chunk_hash):
    # creating dir for file
    file_dir = os.path.join(STORAGE_PATH, file_id)
    os.makedirs(file_dir, exist_ok=True)

    # creating path for content to write
    chunk_file_name = f"{chunk_hash}_{chunk_index}"
    chunk_path = os.path.join(file_dir, chunk_file_name)

    with open(chunk_path, "wb") as f:
        f.write(chunk_data)
    logger.info(f"Stored chunk {chunk_index} for file {file_id} at {chunk_path}")

# TODO some repeated code in this, check if it can be put in commons.py
def replicate_chunk(downstream_nodes, file_id, chunk_index, chunk_data, chunk_hash):
    if not downstream_nodes:
        logger.info(f"No downstream nodes for chunk {chunk_index}. Ending pipeline.")
        return True

    next_node = downstream_nodes[0]
    host, port = next_node.split(":")
    next_downstream = downstream_nodes[1:]

    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((host, int(port)))

        metadata = {
            "type": "replicate_chunk",
            "file_id": file_id,
            "chunk_index": chunk_index,
            "chunk_hash": chunk_hash,
            "downstream": next_downstream
        }

        sock.send(json.dumps(metadata).encode())
        ack = sock.recv(1024)
        if not ack:
            raise Exception("No ACK from downstream node")
        
        sock.sendall(chunk_data)
        
        # Shutdown write side to signal we're done sending
        sock.shutdown(SHUT_WR)
        
        # Now wait for response
        resp = sock.recv(1024)
        sock.close()

        logger.info(f"Replicated chunk {chunk_index} → {next_node}")
        return True

    except Exception as e:
        logger.error(f"Failed to replicate chunk {chunk_index} to {next_node}: {e}")
        return False

def handle_storage(conn, addr):
    # to read the metadata first
    try:
        metadata = conn.recv(4096)

        if not metadata:
            return

        json_metadata = json.loads(metadata.decode())

        # if the below condition satisfies meaning its a "request" on that node
        if json_metadata["type"] in ("write_chunk", "replicate_chunk"):
            file_id = json_metadata["file_id"]
            chunk_hash = json_metadata["chunk_hash"]
            chunk_index = json_metadata["chunk_index"]
            downstream = json_metadata.get("downstream", [])

            # ack that i have received metadata, now u can send the chunk data
            conn.sendall(b"ACK")

            # receiving chunk data
            chunk_data = b""
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                chunk_data += data

            save_chunk(file_id, chunk_index, chunk_data, chunk_hash)

            if downstream:
                replicate_chunk(downstream, file_id, chunk_index, chunk_data, chunk_hash)

            conn.send(b"STORED")
            logger.info(f"Completed write for chunk {chunk_index} (downstream={downstream})")

    except Exception as e:
        logger.error(f"Failed to handle client {addr}: {e}")
    finally:
        conn.close()

def datanode_init():
    sock = create_socket("0.0.0.0", DATANODE_PORT)
    sock.listen()

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_storage, args=(conn, addr), daemon=True).start()
