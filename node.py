import requests
import json

from wallet import Wallet
from DistributedSystems.blockchain import Blockchain
from transaction import Transaction
from block import Block

class Node:
    def __init__(self, host, port, blockchain, wallet, stake=0, is_bootstrap=False, n=None, total_nodes=1):
        self.host = host
        self.port = port
        self.stake_amount = stake  
        self.is_bootstrap = is_bootstrap
        self.api_url = f'http://{host}:{port}/'
        self.blockchain = blockchain
        self.wallet = Wallet()
        self.stakes = {}  # Dictionary to store stakes of other nodes
        self.balances = {}  # Dictionary to store balances of other nodes
        self.nodes = {}  
        
        
        if is_bootstrap:
            self.id_counter = 1  # Αρχικό ID για νέους κόμβους
            self.total_nodes = total_nodes
            self.initialize_genesis_block()


    def initialize_genesis_block(self, total_nodes):
        # Create the initial transaction for the genesis block
        genesis_transaction = Transaction(
            sender_address="0",  # Using 0 as a placeholder for the genesis transaction
            receiver_address=self.wallet.public_key,  # Assuming the wallet has a public_key attribute
            type_of_transaction="genesis",
            amount=1000 * total_nodes,
            message="Genesis Block Transaction",
            nonce=0  # Nonce can be 0 or any value for the genesis transaction
        )
        
        # Manually set the signature of the genesis transaction to None or any placeholder value
        genesis_transaction.sign_transaction("genesis_signature")

        # Create the genesis block
        genesis_block = Block(
            index=0,
            transactions=[genesis_transaction.to_dict()],  # The block expects a list of transactions
            validator=self.wallet.public_key,  # The bootstrap node acts as the validator for the genesis block
            previous_hash="1"  # As per your requirement
        )
        
        # Add the genesis block to the blockchain
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
        
        node_id = self.node_id_counter
        self.nodes[public_key] = {"id": node_id, "address": node_address}
        self.node_id_counter += 1  # Prepare ID for the next node
        print(f"Node {node_id} registered with public key {public_key}.")

        # Transfer 1000 BCC from the bootstrap node to the new node
        self.transfer_bcc_to_new_node(public_key, 1000)

        # After registering the new node, broadcast the updated nodes and blockchain to all nodes
        self.broadcast_updates()

        return True


    # Niko des ti thelei gia to proof of stake edw 
    def transfer_bcc_to_new_node(self, recipient_public_key, amount):
        """Create and execute a transaction to transfer BCC from the bootstrap node to a new node."""
        # Assuming the bootstrap node's wallet has a method to create a signed transaction
        transaction = self.wallet.create_signed_transaction(
            recipient_public_key, 
            amount, 
            message="Welcome to the network!"
        )
        
        # Add the transaction to the blockchain
        self.blockchain.add_transaction(transaction)

        # Assuming a method to mine transactions and add them as a new block
        self.mine_transactions() 

        print(f"Transferred {amount} BCC to new node with public key {recipient_public_key}.")

    # Nomizw den xreiazetai giati ama mpei node mono o bootstrap mporei na ton valei 
    # def add_node(self, public_key, node_address, balance_amount=0, stake_amount=0):
    #     """
    #     Add a new node to the network.
    #     """
    #     self.nodes[public_key] = node_address
    #     self.update_balance(public_key, balance_amount)
    #     self.update_staking(public_key, stake_amount)


    def stake(self, amount):
        """
        Set the stake amount for the node.
        """
        if amount < 0:
            return False, "Stake amount cannot be negative"
        temptrans = Transaction(self, self.wallet.address, 0, "coins", amount, 0)
        self.broadcast_transaction(self,temptrans)
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
    # Example instantiation and usage
    blockchain = Blockchain()  # Assuming a Blockchain class is defined elsewhere
    wallet = Wallet()  # Assuming a Wallet class is defined elsewhere

    # Node and Bootstrap node details
    node = Node('localhost', 5001, blockchain, wallet)
    bootstrap_url = 'http://localhost:5000'  # URL of the bootstrap node

    # Register with the bootstrap node
    node.register_with_bootstrap(bootstrap_url, wallet.public_key)

    # Other operations like creating transactions, updating blockchain, etc.
