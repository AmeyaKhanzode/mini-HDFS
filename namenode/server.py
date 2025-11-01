import heartbeat_handler
import time
import logging
import threading
from shared.config import MONITOR_INTERVAL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

logger.info("Starting namenode server...")

heartbeat_thread = threading.Thread(target=heartbeat_handler.handle_heartbeats, daemon=True)
heartbeat_thread.start()

def monitor_down_nodes():
    while True:
        down_nodes = heartbeat_handler.check_down_nodes()
        if down_nodes:
            for node in down_nodes:
                logger.warning(f"{node} is down")
        time.sleep(MONITOR_INTERVAL)

monitor_thread = threading.Thread(target=monitor_down_nodes, daemon=True)
monitor_thread.start()

while True:
    time.sleep(60)
'''
will need more threads for reading and stuff
'''