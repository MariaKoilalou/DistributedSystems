from flask import Flask, request, jsonify
from node import Node  # Assuming your Node class is inside a folder named 'network'
from blockchain import Blockchain
from transaction import Transaction
from wallet import Wallet
from uuid import uuid4

app = Flask(__name__)

node = None
# Unique identifier for this node in the network
node_identifier = str(uuid4()).replace('-', '')
registered_nodes = []

@app.route('/register', methods=['POST'])
def register_node():
    values = request.get_json()

    # Check for required fields in the incoming JSON
    if 'public_key' not in values or 'node_address' not in values:
        return "Missing values", 400

    # Add the node to the registered nodes list
    registered_nodes.append({
        'public_key': values['public_key'],
        'node_address': values['node_address']
    })

    response = {
        'message': 'New node has been added',
        'total_nodes': len(registered_nodes),
        'nodes': registered_nodes
    }
    return jsonify(response), 201


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # Assume 'Transaction' class has a method to validate transactions
    new_transaction = Transaction(values)
    if new_transaction.is_valid():
        blockchain.add_transaction(new_transaction)
        return "Transaction added", 201
    else:
        return "Invalid transaction", 406
    

@app.route('/blockchain', methods=['GET'])
def get_full_chain():
    chain_data = [block.to_dict() for block in node.blockchain.chain]  # Convert each block to a dictionary
    response = {
        'chain': chain_data,
        'length': len(chain_data),
    }
    return jsonify(response), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {'message': 'Our chain was replaced'}
    else:
        response = {'message': 'Our chain is authoritative'}
    return jsonify(response), 200

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run a BlockChat node.')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address for the node')
    parser.add_argument('--port', type=int, required=True, help='Port number for the node')
    parser.add_argument('--is_bootstrap', action='store_true', help='Flag to set this node as the bootstrap node')

    args = parser.parse_args()

    blockchain = Blockchain()  # Assuming a Blockchain class is defined elsewhere
    wallet = Wallet()  # Assuming a Wallet class is defined elsewhere

    node = Node(host=args.host, port=args.port, blockchain=blockchain, wallet=wallet, is_bootstrap=args.is_bootstrap)
    if not args.is_bootstrap:
        # Assuming the bootstrap node address is known and passed here
        node.register_with_bootstrap('192.168.1.5:5000')

    app.run(host=args.host, port=args.port)
