# For each chunk, requests placement info from Namenode.
import threading
import random
from socket import *
import json
import logging
import os
from shared.commons import create_socket
from shared.config import BACKEND_HOST, BACKEND_PORT, NAMENODE_PORT, REPLICATION_FACTOR
from heartbeat_handler import get_alive_datanodes

REQ_PORT = 5050

def assign_datanodes(num_chunks):
    # algo to assign chunks
    # returns a dict of where to store {chunk1: [], chunk2: []}
    '''
    {
        chunk_1: [datanode1:5001, datanode2:5002]
        chunk_2: [datanode2:5002, datanode1:5001]
    }
    '''
    alive_datanodes = get_alive_datanodes()

    if REPLICATION_FACTOR > len(alive_datanodes):
        print("cant store rn")

    chunk_placements = {}
    random.shuffle(alive_datanodes)

    for i in range(num_chunks):
        selected_nodes = random.sample(alive_datanodes, REPLICATION_FACTOR)

        chunk_id = f"chunk_{i + 1}"
        chunk_placements[chunk_id] = [f"{node['host']}:{node['port']}" for node in selected_nodes]
        
        random.shuffle(alive_datanodes)
    return chunk_placements

def handle_client(client_sock, addr):
    logger = logging.getLogger(__name__)
    try:
        data = client_sock.recv(1024)
        if not data:
            return

        req_data = json.loads(data.decode())
        if req_data:
            if req_data.get("type") == "write_req":
                # TODO call function to add metadata to metastore after all the replication and storage is done
                filename = req_data.get("filename")
                num_chunks = req_data.get("num_chunks")

                alive_datanodes = get_alive_datanodes()
                if REPLICATION_FACTOR > len(alive_datanodes):
                    client_sock.send(b'{"error": "Not enough datanodes"}')
                    return

                chunk_placements = assign_datanodes(num_chunks)
                client_sock.sendall((json.dumps(chunk_placements) + "\n").encode())
    except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
    finally:
        client_sock.close()

def req_listener():
    logger = logging.getLogger(__name__)
    sock = create_socket("0.0.0.0", REQ_PORT)
    sock.listen()
    logger.info(f"Namenode request listener active on port {REQ_PORT}")

    while True:
        client_sock, addr = sock.accept()
        threading.Thread(
            target=handle_client,
            args=(client_sock, addr),
            daemon=True
        ).start()


            
