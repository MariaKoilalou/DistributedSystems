import requests
import json

from wallet import Wallet
from blockchain import Blockchain
from transaction import Transaction
from block import Block

import argparse


class Node:
    def __init__(self, host, port, blockchain, wallet, stake=0, is_bootstrap=False, n=None, total_nodes=1):
        self.host = host
        self.port = port
        self.stake_amount = stake  
        self.total_nodes = total_nodes
        self.is_bootstrap = is_bootstrap
        self.api_url = f'http://{host}:{port}/'
        self.blockchain = blockchain
        self.wallet = wallet
        self.stakes = {}  # Dictionary to store stakes of other nodes
        self.balances = {}  # Dictionary to store balances of other nodes
        self.nodes = {}  
        
        
        if is_bootstrap:
            self.id_counter = 1  # Αρχικό ID για νέους κόμβους
            self.total_nodes = total_nodes
            self.initialize_genesis_block()


    def initialize_genesis_block(self):
        total_nodes = self.total_nodes
        if len(self.blockchain.chain) == 0:
            genesis_transaction = Transaction(
                sender_address="0",
                receiver_address=self.wallet.public_key,
                type_of_transaction="genesis",
                amount=1000 * total_nodes,
                message="Genesis Block",
                nonce=0
            )
            # Use the wallet's sign_transaction method
            signature = self.wallet.sign_transaction(genesis_transaction.to_dict())
            genesis_transaction.signature = signature  # Directly set the signature attribute
            genesis_block = Block(
                index=0,
                transactions=[genesis_transaction.to_dict()],
                validator=self.wallet.public_key,
                previous_hash="1"
            )
            self.blockchain.add_block(genesis_block)


    def register_with_bootstrap(self, bootstrap_url, public_key):
        response = requests.post(bootstrap_url + '/register', json={'public_key': public_key, 'node_address': self.api_url})
        if response.status_code == 200:
            data = response.json()
            self.nodes[data['node_id']] = data['node_address']
            print('Registered with the bootstrap node')
            return True
        return False
    

    def register_node(self, public_key, node_address):
        """Register a new node in the network, assign it a unique ID, and transfer 1000 BCC to it."""
        if not self.is_bootstrap:
            print("This node is not the bootstrap node.")
            return False
        
        node_id = self.total_nodes
        self.nodes[public_key] = {"id": node_id, "address": node_address}
        self.total_nodes += 1  # Prepare ID for the next node
        print(f"Node {node_id} registered with public key {public_key}.")

        # Transfer 1000 BCC from the bootstrap node to the new node
        self.transfer_bcc_to_new_node(public_key, 1000)

        # # After registering the new node, broadcast the updated nodes and blockchain to all nodes
        # self.broadcast_updates()

        return True


    def transfer_bcc_to_new_node(self, recipient_public_key, amount):
        """
        Create and execute a transaction to transfer BCC from this node to a new node,
        then mint a new block containing this transaction.
        """
        # Step 1: Create a signed transaction using the wallet
        signed_transaction = self.wallet.create_signed_transaction(
            recipient_address=recipient_public_key,
            amount=amount,
            message="Welcome to the network!",
            nonce=self.get_next_nonce()  # Assuming a method to manage nonce
        )

        # Assuming the signed_transaction is a dictionary with all needed fields
        # and Transaction class can initialize from such a dictionary
        transaction = Transaction(**signed_transaction)

        # Step 2: Add the transaction to the transaction pool
        self.blockchain.add_transaction_to_pool(transaction)

        # Step 3: Mint a new block with transactions from the pool
        # Assuming 'mint_block' will handle transaction validation
        self.blockchain.mint_block(self.wallet.public_key)  # Validator is the current node's public key

        print(f"Transferred {amount} BCC to new node with public key {recipient_public_key}.")


    def get_next_nonce(self):
        """
        Retrieve the next nonce for transactions from this node by inspecting the transaction history.
        The nonce is incremented for each new transaction to ensure uniqueness.
        """
        max_nonce = 0  # Start with 0, assuming no transactions yet

        # Iterate through the blockchain to find transactions with this node's address as the sender
        for block in self.blockchain.chain:
            for transaction in block.transactions:
                # Assuming 'transactions' in a block is a list of transaction dictionaries
                # And each transaction dictionary has 'sender_address' and 'nonce' keys
                if transaction['sender_address'] == self.wallet.address:
                    max_nonce = max(max_nonce, transaction['nonce'])

        # The next nonce should be one more than the max found in the transaction history
        return max_nonce + 1


    def stake(self, amount):
        """
        Set the stake amount for the node.
        """
        if amount < 0:
            return False, "Stake amount cannot be negative"
        
        self.stake = amount
        self.stakes[self.wallet.public_key] = amount  # Update the stake amount in the dictionary
        return True, "Stake amount set successfully"

    def validate_block(self, block):
        """
        Validate a block by checking the validator and previous hash.
        """
        # Check if the validator matches the stakeholder
        if block.validator != self.stake:
            return False, "Invalid validator"

        # Retrieve the previous block from the blockchain
        previous_block = self.blockchain.chain[-1]

        # Check if the previous hash in the block matches the hash of the previous block
        if block.previous_hash != previous_block.current_hash:
            return False, "Invalid previous hash"

        return True, "Block validated successfully"

    def validate_transaction(self, transaction):
        """
        Validate the transaction by verifying the signature and checking the sender's wallet balance.
        """
        sender_address = transaction.sender_address #edw den prepei na einai sender_address
        amount = transaction.amount

        # Verify the transaction signature
        if not transaction.verify_signature():
            return False, "Invalid signature"

        # Check if the sender has sufficient balance (considering staked amount)
        if self.wallet.balance - self.stake < amount:
            return False, "Insufficient balance"

        return True, "Transaction validated successfully"

    def broadcast_transaction(self, transaction):
        for node_url in self.nodes.values():
            requests.post(node_url + '/transactions/new', json=transaction.to_dict())
        print('Transaction broadcasted to the network')

    def validate_chain(self, chain):
        """
        Validate the received blockchain by validating each block in it.
        """
        for block in blockchain.chain[1:]:  # Exclude the genesis block
            is_valid, message = self.validate_block(block)
            if not is_valid:
                return False, f"Blockchain validation failed: {message}"

        return True, "Blockchain validation successful"

    def broadcast_block(self, block):
        """
        Broadcast the validated block to all other nodes in the network.
        """
        for node_url in self.nodes.values():
            # Assuming each node has an API endpoint to receive new blocks
            requests.post(f"{node_url}/receive_block", json=block.to_dict())

        print("Block broadcasted to the network")


    def update_balance(self, public_key, amount):
        """
        Update the balance of the account with the given public key.
        """
        self.wallet.update_balance(amount)
        self.balances[public_key] = amount

    def update_staking(self, public_key, staked_amount):
        """
        Update the staking amount for the node with the given public key.
        """
        self.staking_info[public_key] += staked_amount
        # Deduct staked amount from available balance
        self.wallet.deduct_balance(staked_amount)
        self.stakes[public_key] = staked_amount


    def process_transaction(self, transaction):
        """
        Process the transaction and update the account balances and staking information accordingly.
        """
        sender_address = transaction.sender_address
        receiver_address = transaction.receiver_address
        amount = transaction.amount

        # Calculate transaction fees based on the message length (1 BCC per character)
        message_fee = len(transaction.message)  # Assuming 1 BCC per character

        # Total fee charged for the transaction (including message fee)
        total_fee = transaction.fee + message_fee

        # Validate sender's balance (considering staked amount and fees)
        if self.wallet.balance - self.stake - total_fee < amount:
            return False, "Insufficient balance"

        # Update sender's balance (considering staked amount and fees)
        self.update_balance(sender_address, self.balances.get(sender_address, 0) - (amount + total_fee))

        # Update receiver's balance
        self.update_balance(receiver_address, self.balances.get(receiver_address, 0) + amount)

        return True, "Transaction processed successfully"

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a BlockChat node.')
    parser.add_argument('--host', type=str, default='localhost', help='Host address for the node')
    parser.add_argument('--port', type=int, required=True, help='Port number for the node')
    parser.add_argument('--is_bootstrap', action='store_true', help='Flag to set this node as the bootstrap node')

    args = parser.parse_args()
    
    blockchain = Blockchain()  # Assuming a Blockchain class is defined elsewhere
    wallet = Wallet()  # Assuming a Wallet class is defined elsewhere

    node = Node(args.host, args.port, blockchain, wallet, is_bootstrap=args.is_bootstrap)

    if not args.is_bootstrap:
        bootstrap_url = 'http://192.168.1.10:5000'  # Adjust the bootstrap URL as needed
        success = node.register_with_bootstrap(bootstrap_url, node.wallet.public_key)
        if success:
            print("Registration with the bootstrap node was successful.")
        else:
            print("Failed to register with the bootstrap node.")

