import os
from datetime import datetime
import json
import time
from socket import *
import logging
from shared.commons import *
from shared.config import DEAD_NODE_THRESHOLD

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

last_heartbeat = {}         # stores node_id: time_of_heartbeat

def handle_heartbeats():                    # this just gets the heartbeats. need to check for those who dont send heartbeats too
    logger = logging.getLogger(__name__)
    namenode_port = int(os.getenv("NAMENODE_PORT"))
    logger.info(f"Starting heartbeat listener on port {namenode_port}")
    
    try:
        sock = create_socket("0.0.0.0", namenode_port)
        sock.listen(5)
        logger.info("Namenode ready to receive heartbeats...")

        while True:
            client_sock, client_addr = sock.accept()
            logger.debug(f"Got connection from {client_addr}")

            data = client_sock.recv(1024)

            if data:
                try:
                    heartbeat_data = json.loads(data.decode())
                    if heartbeat_data.get("type") == "heartbeat" and heartbeat_data.get("status") == "alive":
                        node_id = heartbeat_data.get("node_id")
                        last_heartbeat[node_id] = datetime.now()
                        logger.info(f"Heartbeat received from {node_id}. Status: Alive")
                except Exception as e:
                    logger.error(f"Could not parse JSON data. Error: {e}")
            client_sock.close()
    except Exception as e:
        logger.error(f"Error in heartbeats: {e}")
    finally:
        sock.close()

def check_down_nodes():
    logger = logging.getLogger(__name__)
    now = datetime.now()

    down_nodes = []

    for node_id, last_heartbeat_time in last_heartbeat.items():
        delta = (now - last_heartbeat_time).total_seconds()
        if delta > DEAD_NODE_THRESHOLD:
            down_nodes.append(node_id)
            logger.warning(f"{node_id} is down, last connected at {last_heartbeat_time}")

    return down_nodes 