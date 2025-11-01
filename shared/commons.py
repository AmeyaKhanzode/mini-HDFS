from socket import *
import time
import logging
import os


def create_socket(bind_addr, port):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)    # so u dont have to wait for restart
    sock.bind((bind_addr, port))

    return sock
