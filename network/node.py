import socket
import threading
import sys


class Node:
    def __init__(self, host, port, n):
        self.host = host
        self.port = port
        self.n = n  # Total number of nodes or multiplier for initial coin distribution
        self.blockchain = []
        self.connections = []  # Initialize the connections list
        # Automatically designate the first node as the bootstrap based on a condition
        if self.port == 8001:  # Assuming port 8000 is reserved for the bootstrap node
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = {
            'previous_hash': 1,
            'validator': 0,
            'transactions': [{'to': self.port, 'amount': 1000*n}] 
        }
        self.blockchain.append(genesis_block)
        print("Genesis block created")

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Node listening on {self.host}:{self.port}")

        while True:
            client, address = server.accept()
            self.connections.append(client)
            threading.Thread(target=self.handle_client, args=(client, address)).start()

    def handle_client(self, client, address):
        print(f"Connected to {address}")
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                if message:
                    print(f"Message from {address}: {message}")
            except:
                break
        client.close()

    def connect_to_peer(self, peer_host, peer_port):
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((peer_host, peer_port))
        self.connections.append(peer)
        print(f"Connected to peer at {peer_host}:{peer_port}")
        # Here you can implement further communication with the peer

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python node.py [host] [port] [n]")
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        n = int(sys.argv[3])  # Add this line to capture 'n' from command line arguments
        node = Node(host, port, n)
        node.start_server()

