from flask import Flask, request, jsonify
from node import Node  # Assuming your Node class is inside a folder named 'network'
from blockchain import Blockchain
from transaction import Transaction

app = Flask(__name__)
# This list will store registered nodes
registered_nodes = []
blockchain = Blockchain()
 
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
