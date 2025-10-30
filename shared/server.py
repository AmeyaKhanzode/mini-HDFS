from socket import *

class Server:
    def create_namenode_socket():
        sock = socket(AF_PACKET, SOCK_RAW)
        sock.bind(("0.0.0.0", 5000))

    def create_datanode_socket(node_id):
        if node_id == 1:
            sock = socket(AF_PACKET, SOCK_RAW)
            sock.bind("namenode", 5001)
        if node_id == 2:
            sock = socket(AF_PACKET, SOCK_RAW)
            sock.bind("namenode", 5002)

