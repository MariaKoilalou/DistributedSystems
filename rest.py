import logging
from threading import Thread, Event
from flask.logging import default_handler
from flask import Flask, request, jsonify
import requests
from block import Block
from node import Node  # Assuming your Node class is inside a folder named 'network'
from blockchain import Blockchain
from transaction import Transaction
from uuid import uuid4
import os 

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
        
        
        assigned_node_id = node.next_node_id
        print(f"Current node: {assigned_node_id}")
        
        # Use public_key as the unique identifier for simplicity
        if public_key in node.nodes:
            print(f"Node with public key {public_key} is already registered.")
            return False, None
        
        node.nodes[assigned_node_id] = {'public_key': public_key, 'address': node_address}
        node.next_node_id += 1

        print(f"Node {assigned_node_id} registered.")

        node.transfer_bcc_to_new_node(public_key, 1000)

        print(f"Total nodes: {node.total_nodes}")

        blockchain_data = []
        for block in node.blockchain.chain:
            block_dict = block.to_dict()  # Assuming Block has a to_dict method
            block_dict['transactions'] = [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in block.transactions]
            blockchain_data.append(block_dict)


        broadcast_blockchain()

        if node.next_node_id == node.total_nodes:
            node.broadcast_all()
        
        nodes_data = {
            node_id: {
                'address': node_info['address'],
                'public_key': node_info['public_key']
            }
            for node_id, node_info in node.nodes.items()
        }

        response = {
            'message': 'New node registered successfully',
            'node_id': assigned_node_id,  # Include the node ID in the response
            'node_address': node_address,
            'total_nodes': [node_info['address'] for node_info in node.nodes.values()],
            'blockchain': blockchain_data,
            'nodes': nodes_data
        }
        return jsonify(response), 200
    except Exception as e:
        logger.exception("Failed to register node: %s", e)
        return jsonify({'error': 'Internal server error'}), 500    

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # Assume 'Transaction' class has a method to validate transactions
    new_transaction = Transaction(
                sender_address=values['sender_address'],
                receiver_address=values['receiver_address'],
                type_of_transaction=values['type_of_transaction'],
                amount=values['amount'],  
                message=values['message'],
                nonce=values['nonce'],
            )
    new_transaction.signature = values['signature']
    if node.validate_transaction(new_transaction):
        blockchain.add_transaction_to_pool(new_transaction)
        node.mint_block()
        return jsonify({'error': 'Transaction broadcasted'}), 200
    else:
        return jsonify({'error': 'Invalid transaction'}), 400
    
@app.route('/receive_block', methods=['POST'])
def new_block():
    values = request.get_json()
    # Assume 'Transaction' class has a method to validate transactions
    new_block = Block(index=values['index'], transactions=values['transactions'], validator=values['validator'], previous_hash=values['previous_hash'])
    new_block.current_hash = new_block.calculate_hash()
    node.add_block(new_block)
    if node.validate_block(new_block):
        blockchain.add_block(new_block)
        return jsonify({'error': 'Block broadcasted'}), 200
    else:
        return jsonify({'error': 'Invalid block'}), 400
    
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
        incoming_chain = request.get_json()
        if not incoming_chain:
            return jsonify({'error': 'Invalid data received'}), 400

        current_chain_backup = node.blockchain.chain
        node.blockchain.chain = [Block(**block_data) for block_data in incoming_chain]

        if node.blockchain.validate_chain():
            current_len = len(current_chain_backup)
            incoming_len = len(node.blockchain.chain)

            if incoming_len > current_len:
                # Convert the blockchain into a format that can be JSON-serialized
                updated_chain = [block.to_dict() for block in node.blockchain.chain]  # Assuming each Block has a `to_dict` method
                return jsonify({'message': 'Blockchain updated successfully', 'new_chain': updated_chain}), 200
            else:
                node.blockchain.chain = current_chain_backup
                return jsonify({'message': 'Received chain is not longer than the current chain'}), 200
        else:
            node.blockchain.chain = current_chain_backup
            return jsonify({'error': 'Received chain is invalid'}), 400
    except Exception as e:
        # Assuming `logger` is defined and configured elsewhere in your code
        logger.exception("Failed to update blockchain: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/receive_data', methods=['POST'])
def receive_nodes():
    try:
        received_data = request.get_json()
        node.update_nodes(received_data)
        return jsonify({'message': 'Node updated successfully'}), 200
    except Exception as e:
        logger.exception("Failed to receive node: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/broadcast_blockchain', methods=['POST'])
def broadcast_blockchain():
    node_addresses = [node_info["address"] for node_id, node_info in node.nodes.items()]
    
    # Convert each block to a dictionary, including converting each transaction to a dictionary
    blockchain_data = []
    for block in node.blockchain.chain:
        block_dict = block.to_dict()  # Assuming Block has a to_dict method
        # Check if each transaction is a dict or needs conversion
        block_dict['transactions'] = [tx if isinstance(tx, dict) else tx.to_dict() for tx in block.transactions]
        blockchain_data.append(block_dict)

    for node_address in node_addresses:
        if node_address == node.api_url:  # Skip broadcasting to self
            continue
        try:
            # Send the serialized blockchain data
            response = requests.post(f"{node_address}/update_blockchain", json=blockchain_data)
            if response.status_code == 200:
                print(f"Successfully broadcasted blockchain to {node_address}.")
            else:
                print(f"Failed to broadcast blockchain to {node_address}. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error broadcasting blockchain to {node_address}: {e}")



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
        print(f"Total stakes are {node.calculate_stakes(node.blockchain.chain, node.wallet.public_key)}")


    # CLI Thread
    cli_thread = Thread(target=cli.run_cli, args=(node, shutdown_event))
    cli_thread.start()

    try:
        app.run(host=args.host, port=args.port)
    finally:
        # This is executed when app.run() exits
        shutdown_event.set()  # Signal CLI thread to shut down
        cli_thread.join()  # Wait for the CLI thread to exit
        print("Flask app and CLI have shut down.")



