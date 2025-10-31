from socket import *

def create_socket(bind_addr, port):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind((bind_addr, port))

    return sock