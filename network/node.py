import requests
import json

from blockchain.chain import Blockchain
from wallet.wallet import Wallet

class Node:
    def __init__(self, host, port, blockchain, wallet):
        self.host = host
        self.port = port
        self.api_url = f'http://{host}:{port}/'
        self.blockchain = blockchain
        self.wallet = wallet
        self.nodes = {}  # Other nodes' public keys mapped to their network addresses

    def register_with_bootstrap(self, bootstrap_url, public_key):
        response = requests.post(bootstrap_url + '/register', json={'public_key': public_key, 'node_address': self.api_url})
        if response.status_code == 200:
            data = response.json()
            self.nodes[data['node_id']] = data['node_address']
            print('Registered with the bootstrap node')
            return True
        return False

    def broadcast_transaction(self, transaction):
        for node_url in self.nodes.values():
            requests.post(node_url + '/transactions/new', json=transaction.to_dict())
        print('Transaction broadcasted to the network')

    def update_blockchain(self):
        longest_chain = None
        current_len = len(self.blockchain.chain)

        for node_url in self.nodes.values():
            response = requests.get(node_url + '/blockchain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > current_len and self.blockchain.validate_chain(chain):
                    current_len = length
                    longest_chain = chain

        if longest_chain:
            self.blockchain.chain = longest_chain
            return True
        return False

    def add_node(self, public_key, node_address):
        self.nodes[public_key] = node_address

if __name__ == '__main__':
    # Example instantiation and usage
    blockchain = Blockchain()  # Assuming a Blockchain class is defined elsewhere
    wallet = Wallet()  # Assuming a Wallet class is defined elsewhere

    # Node and Bootstrap node details
    node = Node('localhost', 5001, blockchain, wallet)
    bootstrap_url = 'http://localhost:5000'  # URL of the bootstrap node

    # Register with the bootstrap node
    node.register_with_bootstrap(bootstrap_url, wallet.public_key)

    # Other operations like creating transactions, updating blockchain, etc.

