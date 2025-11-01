import os

NAMENODE_HOST = os.getenv("NAMENODE_HOST", "namenode")
NAMENODE_PORT = int(os.getenv("NAMENODE_PORT", 5000))

# time stuff
HEARTBEAT_INTERVAL = 3
CONNECTION_RETRY_DELAY = 2
DEAD_NODE_THRESHOLD = 9
MONITOR_INTERVAL = 5

'''
when shifting to real machines, make sure to change the env variables by running:

export NAMENODE_HOST=192.168.0.101
export DATANODE1_HOST=192.168.0.102
export DATANODE2_HOST=192.168.0.103

'''

DATANODES = [
    {
        "id": "datanode1",
        "host": "datanode1",
        "port": 5001
    },
    {
        "id": "datanode2",
        "host": "datanode2",
        "port": 5002
    }
]