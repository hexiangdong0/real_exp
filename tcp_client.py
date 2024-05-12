
import os
import socket
import sys
import time
from datetime import datetime
import subprocess

def random_data_generator(size, total_size):
    """生成指定大小的随机数据块，直到达到总大小"""
    bytes_sent = 0
    while bytes_sent < total_size:
        yield os.urandom(min(size, total_size - bytes_sent))
        bytes_sent += size

def send(host, port, generator, ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind((local_ip, local_port))
    sock.connect((host, port))
    for data_block in generator:
        sock.send(data_block)

def gett():
    return datetime.now().strftime('%Y.%m.%d %H:%M:%S')

# python -c "from tcp_client import *; send('47.120.20.89', 65432, random_data_generator(4096, 10240000))"
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python tcp_client.py [host] [port]')
        sys.exit(0)
    host, port, = sys.argv[1 : 3]
    port = int(port)

    total_bytes = 600 * 1024 * 1024
    generator = random_data_generator(4096, total_bytes)
    send(host, port, generator)
