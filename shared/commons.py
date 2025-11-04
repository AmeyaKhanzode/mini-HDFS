from socket import *


def create_socket(bind_addr, port):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)    # so u dont have to wait for restart
    sock.bind((bind_addr, port))

    return sock

def read_till_newline(sock, buffer_size=4096):
    data = b""

    while b"\n" not in data:
        chunk = sock.recv(buffer_size)
        if not chunk:
            raise ConnectionError("some shit happened in reading chunks")
        data += chunk
    return data.decode().strip()