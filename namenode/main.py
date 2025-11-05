# For each chunk, requests placement info from Namenode.
import uuid
import threading
import random
from socket import *
import json
import logging
import os
from shared.commons import create_socket, read_till_newline
from shared.config import BACKEND_HOST, BACKEND_PORT, NAMENODE_REQ_PORT, REPLICATION_FACTOR
from heartbeat_handler import get_alive_datanodes
from db_utils import store_file_metadata, get_file_metadata, get_chunk_locations, list_all_files
from ping3 import ping

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
        "file_id": "b10a2f8a-97a5-4d30-becb-2a76d...",  # temp UUID
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

    # temp uuid for now, will be renamed after chunks are uploaded
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
        data = read_till_newline(client_sock)
        if not data:
            return

        req_data = json.loads(data)
        if req_data:
            if req_data.get("type") == "read_req":
                subtype = req_data.get("subtype")
                
                if subtype == "list_files":
                    # Get all files from database
                    files = list_all_files()
                    response = {"status": "ok", "files": files}
                    client_sock.sendall((json.dumps(response) + "\n").encode())
                elif subtype == "read_file":
                    """
                    incoming data is probably like:
                    {
                        "type": "read_req",
                        "subtype": "read_file",
                        "filename": "changes.md"
                    }
                    """
                    filename = req_data.get("filename")

                    file_metadata = get_file_metadata(filename)
                    file_hash = file_metadata.get("file_hash") if file_metadata else None
                    
                    if file_hash is not None:
                        chunk_locations = get_chunk_locations(file_hash)

                        """
                        chunk_locations should look something like this:
                            {
                                "0": {
                                    "chunk_hash": j09s10j90h819hhasjdk10912asda,
                                    "datanodes": ["datanode1:5001", "datanode:5002"]
                                }
                                "1": {
                                    "chunk_hash": jkasdhu12hwkjhsa90d1982hudau1,
                                    "datanodes": ["datanode2:5002", "datanode1:5001"]
                                }
                            }
                        """
                        try:
                            indices = sorted(chunk_locations.keys(), key=lambda k: int(k))
                        except Exception:
                            indices = list(chunk_locations.keys())

                        chunk_host_map = {}

                        for chunk_index in indices:
                            datanodes = chunk_locations[chunk_index]["datanodes"]
                            chunk_hash = chunk_locations[chunk_index]["chunk_hash"]

                            # find the first node thats actually up from the list
                            found_up_node = False
                            for node in datanodes:
                                parts = node.split(":")
                                if len(parts) != 2:
                                    logger.error(f"Invalid datanode format: {node}")
                                    continue
                                    
                                host = parts[0]
                                port = parts[1]

                                if ping(host):
                                    found_up_node = True
                                    chunk_host_map[f"{chunk_hash}_{chunk_index}"] = f"{host}:{port}"
                                    break
                            
                            if not found_up_node:
                                logger.error(f"No datanodes available for chunk: {chunk_hash}")
                                error_msg = {"status": "error", "message": "no available datanode"}
                                client_sock.sendall((json.dumps(error_msg) + "\n").encode())
                                return

                        client_sock.sendall((json.dumps({
                            "status": "ok",
                            "file_hash": file_hash,
                            "chunk_map": chunk_host_map
                        }) + "\n").encode())
                        logger.info(f"Sending chunk map to the backend")
                    else:
                        error_msg = {"status": "error", "message": "File doesn't exist"}
                        client_sock.sendall((json.dumps(error_msg) + "\n").encode())
                            
                else:
                    response = {"status": "error", "message": "Unknown read subtype"}
                    client_sock.sendall((json.dumps(response) + "\n").encode())

            elif req_data.get("type") == "write_req":
                filename = req_data.get("filename")
                num_chunks = req_data.get("num_chunks")

                alive_datanodes = get_alive_datanodes()

                chunk_placements = assign_datanodes(num_chunks)
                client_sock.sendall((json.dumps(chunk_placements) + "\n").encode())
            
            elif req_data.get("type") == "metadata_write":
                filename = req_data.get("filename")
                file_hash = req_data.get("file_hash")
                file_size = req_data.get("file_size")
                num_chunks = req_data.get("num_chunks")
                placements = req_data.get("placements")
                chunk_hashes = req_data.get("chunk_hashes", [])
                
                # Store metadata in database
                success = store_file_metadata(file_hash, filename, file_size, num_chunks, placements, chunk_hashes)
                
                if success:
                    logger.info(f"Stored metadata for {filename} (hash: {file_hash})")
                    response = {"status": "ok"}
                else:
                    logger.error(f"Failed to store metadata for {filename}")
                    response = {"status": "error"}
                
                client_sock.sendall((json.dumps(response) + "\n").encode())
                
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


            
