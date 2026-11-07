# does everything
import time
import heartbeat_handler
import threading
import logging
from shared.config import DATANODE_ID
from main import datanode_init

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Starting datanode {DATANODE_ID}...")

heartbeat_thread = threading.Thread(target=heartbeat_handler.send_heartbeat, daemon=True)
heartbeat_thread.start()

read_write_thread = threading.Thread(target=datanode_init, daemon=True)
read_write_thread.start()

while True:
    time.sleep(60)