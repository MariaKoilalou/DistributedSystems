import socket
import sys

def connect_and_send(host, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(message.encode('utf-8'))
        print(f"Sent message to {host}:{port}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python p2p.py [target_host] [target_port] [message]")
        sys.exit(1)

    target_host = sys.argv[1]
    target_port = int(sys.argv[2])
    message = sys.argv[3]
    connect_and_send(target_host, target_port, message)


