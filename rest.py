import logging
from threading import Thread, Event
from flask.logging import default_handler
from flask import Flask, request, jsonify
from block import Block
from node import Node  # Assuming your Node class is inside a folder named 'network'
from blockchain import Blockchain
from transaction import Transaction
from wallet import Wallet
from uuid import uuid4

import cli 

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(default_handler)

shutdown_event = Event()

node = None
# Unique identifier for this node in the network
node_identifier = str(uuid4()).replace('-', '')


@app.route('/register', methods=['POST'])
def register():
    try:
        values = request.get_json()
        
        # Extract the public key and node address from the incoming JSON
        public_key = values.get('public_key')
        node_address = values.get('node_address')

        # Validate the incoming data
        if not public_key or not node_address:
            return jsonify({'message': 'Missing public key or node address'}), 400
        
        success, node_id = node.register_node(public_key, node_address)
        blockchain_data = [block.to_dict() for block in node.blockchain.chain]

        # Use the register_node method from the Node class to add the new node
        if success:
            response = {
                'message': 'New node registered successfully',
                'node_id': node_id,  # Include the node ID in the response
                'node_address': node_address,
                'total_nodes': [node_info['address'] for node_info in node.nodes.values()],
                'blockchain': blockchain_data
            }
            return jsonify(response), 200
        else:
            return jsonify({'message': 'Node registration failed'}), 500
    except Exception as e:
        logger.exception("Failed to register node: %s", e)
        return jsonify({'error': 'Internal server error'}), 500    


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

@app.route('/update_blockchain', methods=['POST'])
def update_blockchain():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid data received'}), 400

        if node.update_blockchain(data):
            return jsonify({'message': 'Blockchain updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update blockchain'}), 500
    except Exception as e:
        logger.exception("Failed to update blockchain: %s", e)
        return jsonify({'error': 'Internal server error'}), 505


@app.route('/receive_data', methods=['POST'])
def receive_nodes():
    try:
        received_data = request.get_json()
        node.update_nodes(received_data)
        return jsonify({'message': 'Node updated successfully'}), 200
    except Exception as e:
        logger.exception("Failed to receive node: %s", e)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/trigger_broadcast', methods=['POST'])
def trigger_broadcast():
    # Trigger the broadcast_all method on the bootstrap node
    node.broadcast_all()
    return jsonify({'message': 'Broadcast triggered successfully'}), 200

@app.route('/broadcast_blockchain', methods=['POST'])
def broadcast_blockchain():
    node.broadcast_blockchain()
    return jsonify({'message': 'Broadcast triggered successfully'}), 200

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run a BlockChat node.')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address for the node')
    parser.add_argument('--port', type=int, required=True, help='Port number for the node')
    parser.add_argument('--is_bootstrap', action='store_true', help='Flag to set this node as the bootstrap node')
    parser.add_argument('--bootstrap_url', type=str, help='URL of the bootstrap node for registration')

    args = parser.parse_args()

    blockchain = Blockchain()  # Assuming a Blockchain class is defined elsewhere

    node = Node(host=args.host, port=args.port, blockchain=blockchain, is_bootstrap=args.is_bootstrap)
    
    # Node registration logic
    if not args.is_bootstrap and args.bootstrap_url:
        success = node.register_with_bootstrap(args.bootstrap_url, node.wallet.public_key)
        if success:
            print("Registration with the bootstrap node was successful.")
        else:
            print("Failed to register with the bootstrap node.")

    balance = node.check_balance()
    print(f"node balance: {balance} BCC")

    # CLI Thread
    cli_thread = Thread(target=cli.run_cli, args=(node, blockchain, shutdown_event))
    cli_thread.start()

    try:
        app.run(host=args.host, port=args.port)
    finally:
        # This is executed when app.run() exits
        shutdown_event.set()  # Signal CLI thread to shut down
        cli_thread.join()  # Wait for the CLI thread to exit
        print("Flask app and CLI have shut down.")