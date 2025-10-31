import os

NAMENODE_HOST = os.getenv("NAMENODE_HOST", "namenode")
NAMENODE_PORT = int(os.getenv("NAMENODE_PORT", 5000))

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