from socket import *
import threading
import hashlib
import json
import os
import logging
from shared.commons import create_socket
from shared.config import DATANODE_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STORAGE_PATH = os.path.expanduser("/data")
os.makedirs(STORAGE_PATH, exist_ok=True)

def handle_storage(conn, addr):
    # to read the metadata first
    try:
        metadata = conn.recv(4096)

        if not metadata:
            return

        json_metadata = json.loads(metadata.decode())

        if json_metadata["type"] == "write_chunk":
            file_id = json_metadata["file_id"]
            chunk_hash = json_metadata["chunk_hash"]
            chunk_index = json_metadata["chunk_index"]

            conn.sendall(b"ACK")

            file_dir = os.path.join(STORAGE_PATH, file_id)
            os.makedirs(file_dir, exist_ok=True)

            chunk_file_name = f"{chunk_hash}_{chunk_index}"
            chunk_path = os.path.join(file_dir, chunk_file_name)

            chunk_data = b""
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                chunk_data += data

            with open(chunk_path, "wb") as f:
                f.write(chunk_data)
            
            verify_hash = hashlib.sha256(chunk_data).hexdigest()
            if verify_hash != chunk_hash:
                logger.error(f"Hash mismatch for {chunk_file_name}")
                conn.sendall(b"HASH_MISMATCH")
            else:
                logger.info(f"Stored {chunk_file_name} ({len(chunk_data)} bytes)")
                conn.sendall(b"STORED")

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
