from flask import Flask, request, jsonify
import requests

from node import Node
from blockchain.chain import Blockchain
from blockchain.block import Block
from blockchain.transaction import Transaction





app = Flask(__name__)

# Assuming 'Blockchain', 'Transaction', and 'Node' classes are defined elsewhere
blockchain = Blockchain()
node = Node()

@app.route('/register', methods=['POST'])
def register_node():
    values = request.get_json()
    node.register(values['public_key'], values['node_address'])
    return "Node registered", 200

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
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
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

@app.route('/broadcast/block', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    block = values['block']
    # Assume 'Blockchain' class has a method to validate and add blocks
    if blockchain.add_block(block):
        return "Block added", 200
    else:
        return "Block rejected", 406

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


