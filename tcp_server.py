# 接收文件
import socket
import threading

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    total_data_received = 0
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            total_data_received += len(data)
        print(f"Total data received from {addr}: {total_data_received} bytes")

def start_server(host='0.0.0.0', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Server listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()
