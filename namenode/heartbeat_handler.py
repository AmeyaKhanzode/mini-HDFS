from datetime import datetime
import json
import time
import threading
from socket import *
import logging
from shared.commons import *
from shared.config import DEAD_NODE_THRESHOLD, NAMENODE_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

datanode_registry = {}      # stores details about all of the datanodes
registry_lock = threading.Lock()  # Lock to prevent race conditions

def handle_heartbeats():                    # this just gets the heartbeats. need to check for those who dont send heartbeats too
    logger = logging.getLogger(__name__)
    logger.info(f"Starting heartbeat listener on port {NAMENODE_PORT}")
    
    try:
        sock = create_socket("0.0.0.0", NAMENODE_PORT)
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
                        datanode_id = heartbeat_data.get("datanode_id")
                        host = heartbeat_data.get("host")
                        port = heartbeat_data.get("port")
                        status = heartbeat_data.get("status", "alive")
                        
                        with registry_lock:
                            if not datanode_registry.get(datanode_id):
                                datanode_registry[datanode_id] = {
                                    "host": host,
                                    "port": port,
                                    "last_beat": datetime.now(),
                                    "status": "alive",
                                }
                            else:
                                datanode_registry[datanode_id]["last_beat"] = datetime.now()
                                datanode_registry[datanode_id]["status"] = "alive"
                        
                        logger.info(f"Heartbeat received from {datanode_id}. Status: Alive")
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

    with registry_lock:
        for node_id, node_info in datanode_registry.items():
            last_heartbeat_time = node_info.get("last_beat")
            
                
            delta = (now - last_heartbeat_time).total_seconds()
            if delta > DEAD_NODE_THRESHOLD:
                down_nodes.append(node_id)
                node_info["status"] = "down"
                logger.warning(f"{node_id} is down, last connected at {last_heartbeat_time}")
            else:
                node_info["status"] = "alive"

    return down_nodes 


def get_alive_datanodes():
    with registry_lock:
        return [{"id": node_id, "host": node_info["host"], "port": node_info["port"]} for node_id, node_info in datanode_registry.items() if node_info["status"] == "alive"]

def get_all_datanodes():
    check_down_nodes()
    with registry_lock:
        nodes = []
        for node_id, node_info in datanode_registry.items():
            nodes.append({
                "id": node_id,
                "host": node_info["host"],
                "port": node_info["port"],
                "status": node_info["status"],
                "last_heartbeat": node_info["last_beat"].isoformat() if node_info.get("last_beat") else None
            })
        return nodes
