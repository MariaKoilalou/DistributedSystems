import json
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
            'transaction_pool': node.blockchain.transaction_pool,
            'nodes': nodes_data
        }
        return jsonify(response), 200
    except Exception as e:
        logger.exception("Failed to register node: %s", e)
        return jsonify({'error': 'Internal server error'}), 500    

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    new_transaction = Transaction(
                sender_address=values['sender_address'],
                receiver_address=values['receiver_address'],
                type_of_transaction=values['type_of_transaction'],
                amount=values['amount'],  
                message=values['message'],
                nonce=values['nonce'],
            )
    
    new_transaction.sign_transaction(values['private_key'])

    if node.validate_transaction(new_transaction):
        node.blockchain.add_transaction_to_pool(new_transaction.to_dict())
        node.mint_block()
        return jsonify({'error': 'Transaction broadcasted'}), 200
    else:
        return jsonify({'error': 'Invalid transaction'}), 400
    

@app.route('/receive_block', methods=['POST'])
def new_block():
    values = request.get_json()

    # Log the received values for debugging purposes
    print("Received data for new block:", values)

    # Instantiate the Block here
    new_block = Block(
        index=values['index'],
        transactions=values['transactions'],
        validator=values['validator'],
        previous_hash=values['previous_hash'],
        capacity = node.blockchain.block_capacity
    )

    if node.validate_block(new_block):
        node.blockchain.add_block(new_block)
        return jsonify({'message': 'Block added and broadcasted'}), 200
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

@app.route('/update_blockchain', methods=['POST'])
def update_blockchain():
    try:
        data = request.get_json()
        incoming_chain = data['blockchain_data']

        if not incoming_chain:
            return jsonify({'error': 'Invalid data received'}), 400

        current_chain_backup = node.blockchain.chain
        node.blockchain.chain = [Block(**block_data) for block_data in incoming_chain]
        node.blockchain.transaction_pool = data['transaction_pool']
        if node.blockchain.validate_chain():
            current_len = len(current_chain_backup)
            incoming_len = len(node.blockchain.chain)

            if incoming_len > current_len:
                updated_chain = [block.to_dict() for block in node.blockchain.chain]  
                return jsonify({'message': 'Blockchain updated successfully', 'new_chain': updated_chain}), 200
            else:
                node.blockchain.chain = current_chain_backup
                return jsonify({'message': 'Received chain is not longer than the current chain'}), 200
        else:
            node.blockchain.chain = current_chain_backup
            return jsonify({'error': 'Received chain is invalid'}), 400
    except Exception as e:
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

    for node_address in node_addresses[:-1]:
        try:
            # Send the serialized blockchain data
            response = requests.post(f"{node_address}/update_blockchain", json={'blockchain_data': blockchain_data, 'transaction_pool': node.blockchain.transaction_pool})
            if response.status_code == 200:
                print(f"Successfully broadcasted blockchain to {node_address}.")
            else:
                print(f"Failed to broadcast blockchain to {node_address}. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error broadcasting blockchain to {node_address}: {e}")
from flask import request

@app.route('/start_test', methods=['POST'])
def start_test():
    data = request.get_json()
    transactions_folder = data.get('transactions_folder')
    node_id = node.get_node_id_by_public_key(node.wallet.public_key)
    if transactions_folder:
        node.start_transaction_test(transactions_folder, node_id)
        return jsonify({'message': f'Transaction tests started for all nodes using folder {transactions_folder}'}), 200
    else:
        return jsonify({'error': 'Missing transactions_folder in JSON data'}), 400


def report_transactions(self, transaction_count):
        # This function would be called to report this node's transaction count to the central node
        central_node_url = "http://central-node-address:port/report"  # Adjust this to your central node's address
        try:
            response = requests.post(central_node_url, json={'node_id': self.node_id, 'transactions': transaction_count})
            if response.status_code == 200:
                print("Reported transaction count successfully")
            else:
                print("Failed to report transaction count")
        except requests.exceptions.RequestException as e:
            print(f"Error reporting transaction count: {e}")

@app.route('/receive_metrics', methods=['POST'])
def receive_metrics():
    received_metrics = request.get_json()
    node_id = received_metrics.get('node_id')

    # Save the metrics to a file
    save_metrics_to_file(node_id, received_metrics)

    # Broadcast the received metrics to all other nodes
    broadcast_metrics_to_all_nodes(received_metrics)

    return jsonify({'message': 'Metrics received and broadcasted'}), 200

def save_metrics_to_file(node_id, metrics):
    directory_path = 'test_results'
    os.makedirs(directory_path, exist_ok=True)
    filepath = os.path.join(directory_path, f'metrics_node_{node_id}.txt')
    
    with open(filepath, 'w') as file:
        file.write(json.dumps(metrics))
    
    # After saving, check if all metrics are received
    check_and_aggregate_metrics(node.total_nodes, directory_path, 'aggregated_metrics.txt')

def broadcast_metrics_to_all_nodes(metrics):
    for node_id, node_info in node.nodes.items():
        if node_id != metrics['node_id']:  # Avoid sending back to the sender
            try:
                response = requests.post(f"{node_info['address']}/receive_metrics", json=metrics)
                if response.status_code == 200:
                    print(f"Metrics successfully broadcasted to node {node_id}")
                else:
                    print(f"Failed to broadcast metrics to node {node_id}. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error broadcasting metrics to node {node_id}: {e}")

def check_and_aggregate_metrics(total_nodes, folder_path, output_filename):
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    if len(files) == total_nodes:
        node.aggregate_metrics(total_nodes, folder_path, output_filename)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run a BlockChat node.')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address for the node')
    parser.add_argument('--port', type=int, required=True, help='Port number for the node')
    parser.add_argument('--is_bootstrap', action='store_true', help='Flag to set this node as the bootstrap node')
    parser.add_argument('--bootstrap_url', type=str, help='URL of the bootstrap node for registration')
    parser.add_argument('--block_capacity', type=int, default=5, help='Block capacity for the blockchain')
    parser.add_argument('--total_nodes', type=int, default=5, help='Total number of nodes in the network')

    args = parser.parse_args()

    # Initialize Blockchain with specified block capacity
    blockchain = Blockchain(block_capacity=args.block_capacity)

    # Initialize Node with specified total nodes and blockchain instance
    node = Node(host=args.host, port=args.port, blockchain=blockchain, is_bootstrap=args.is_bootstrap, total_nodes=args.total_nodes)

    
    # Node registration logic
    if not args.is_bootstrap and args.bootstrap_url:
        success = node.register_with_bootstrap(args.bootstrap_url, node.wallet.public_key)
        if success:
            print("Registration with the bootstrap node was successful.")
        else:
            print("Failed to register with the bootstrap node.")


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



