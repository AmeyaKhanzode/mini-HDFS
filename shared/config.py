import os

CHUNK_SIZE = 2 * 1024 * 1024 # 2mb

NAMENODE_HOST = os.getenv("NAMENODE_HOST", "namenode")
NAMENODE_PORT = int(os.getenv("NAMENODE_PORT", 5000))

# Current datanode configuration (set per datanode container)
DATANODE_HOST = os.getenv("DATANODE_HOST", "localhost")
DATANODE_PORT = int(os.getenv("DATANODE_PORT", 5001))

DATANODE1_HOST = os.getenv("DATANODE1_HOST", "datanode1")
DATANODE1_PORT = int(os.getenv("DATANODE1_PORT", 5001))

DATANODE2_HOST = os.getenv("DATANODE2_HOST", "datanode2")
DATANODE2_PORT = int(os.getenv("DATANODE2_PORT", 5002))

BACKEND_HOST = os.getenv("BACKEND_HOST", "backend")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))

# time stuff
HEARTBEAT_INTERVAL = 3
CONNECTION_RETRY_DELAY = 2
DEAD_NODE_THRESHOLD = 9
MONITOR_INTERVAL = 5

REPLICATION_FACTOR = 2

'''
when shifting to real machines, make sure to change the env variables by running:

export NAMENODE_HOST=192.168.0.101
export DATANODE1_HOST=192.168.0.102
export DATANODE2_HOST=192.168.0.103

'''

DATANODES = {
    "datanode1": {
        "host": "datanode1",
        "port": 5001
    },
    "datanode2": {
        "host": "datanode2",
        "port": 5002
    }
}