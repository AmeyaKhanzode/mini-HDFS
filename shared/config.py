import os
import socket

CHUNK_SIZE = 2 * 1024 * 1024 # 2mb

NAMENODE_HOST = os.getenv("NAMENODE_HOST", "namenode")
NAMENODE_PORT = int(os.getenv("NAMENODE_PORT", "5000"))  # Heartbeat port
NAMENODE_REQ_PORT = int(os.getenv("NAMENODE_REQ_PORT", "5050"))  # Client request port

# Current datanode configuration (set per datanode container)
# datanodes register themselves with the namenode through heartbeats, so any number of them can join.
# if not set, these fall back to the pod's own hostname / fqdn
# (in a k8s statefulset that's datanode-0 and datanode-0.<headless-service>.<ns>.svc.cluster.local)
DATANODE_ID = os.getenv("DATANODE_ID", socket.gethostname())
DATANODE_HOST = os.getenv("DATANODE_HOST", socket.getfqdn())
DATANODE_PORT = int(os.getenv("DATANODE_PORT", "5001"))

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
export DATANODE_HOST=<this machine's ip>

'''