# does everything
import time
import heartbeat_handler
import threading
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Starting datanode {os.getenv('DATANODE_ID')}...")

heartbeat_thread = threading.Thread(target=heartbeat_handler.send_heartbeat, daemon=True)
heartbeat_thread.start()

while True:
    time.sleep(60)