# does everything
import time
import heartbeat_handler
import threading
import logging
import os
from main import datanode_init

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Starting datanode {os.getenv('DATANODE_ID')}...")

heartbeat_thread = threading.Thread(target=heartbeat_handler.send_heartbeat, daemon=True)
heartbeat_thread.start()

read_write_thread = threading.Thread(target=datanode_init, daemon=True)
read_write_thread.start()

while True:
    time.sleep(60)