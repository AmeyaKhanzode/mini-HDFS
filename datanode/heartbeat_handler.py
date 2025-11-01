import json
import datetime
import os
import logging
import time
from socket import *
from shared.config import DATANODES, HEARTBEAT_INTERVAL, CONNECTION_RETRY_DELAY, NAMENODE_HOST, NAMENODE_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)       # the way it logs

def send_heartbeat():
    logger = logging.getLogger(__name__)
    datanode_id = os.getenv("DATANODE_ID")
    
    while True:
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                sock = socket(AF_INET, SOCK_STREAM)
                sock.connect((NAMENODE_HOST, NAMENODE_PORT))
                heartbeat = {
                    "type": "heartbeat",
                    "status": "alive",
                    "node_id": datanode_id,
                    "datanode_host": DATANODES[datanode_id].get("host"),
                    "datanode_port": DATANODES[datanode_id].get("port"),
                    "status_code": 1
                }
                sock.send(json.dumps(heartbeat).encode())
                sock.close()
                logger.info(f"Heartbeat sent from datanode {datanode_id}")
                break
            except ConnectionRefusedError:
                retry_count += 1
                logger.warning(f"Connection to namenode refused, retrying... ({retry_count}/{max_retries})")
                time.sleep(CONNECTION_RETRY_DELAY)
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")
                break  
        
        if retry_count >= max_retries:
            logger.error("Failed to connect to namenode after max retries.")
        
        time.sleep(HEARTBEAT_INTERVAL)