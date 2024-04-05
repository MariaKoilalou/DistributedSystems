import hashlib
import requests
from wallet import Wallet
from transaction import Transaction
from block import Block
from threading import Lock
import random
import numpy

blockchain_lock = Lock()

class Node:
    def __init__(self, host, port, blockchain, is_bootstrap=False, nonce = 0, total_nodes=5):
        self.host = host
        self.port = port 
        self.total_nodes = total_nodes
        self.is_bootstrap = is_bootstrap
        self.api_url = f'http://{host}:{port}'
        self.blockchain = blockchain
        self.nonce = nonce
        self.wallet = self.generate_wallet()
        self.node_id = 0 if is_bootstrap else None
        self.stakes = {} 
        self.nodes = {}
        
        
        if is_bootstrap:
            self.next_node_id = 1
            self.nodes[self.node_id] = {'public_key': self.wallet.public_key, 'address': self.api_url}
            self.initialize_genesis_block()


    def update_nodes(self, received_nodes_info):
        """Updates the nodes dictionary with the received nodes information."""
        for node_id, node_info in received_nodes_info.items():
            if node_id == self.node_id:
                continue
            self.nodes[node_id] = node_info
        print("Nodes updated successfully")

    def generate_wallet(self):
        return Wallet()

    def initialize_genesis_block(self):
        total_nodes = self.total_nodes

        if len(self.blockchain.chain) == 0:
            genesis_transaction = Transaction(
                sender_address="0",
                receiver_address=self.wallet.public_key,
                type_of_transaction="genesis",
                amount=1000 * total_nodes,  
                nonce=0,
                message="Genesis Block"
            )
            genesis_transaction.sign_transaction(self.wallet.private_key)
            genesis_block = Block(
                index=0,
                transactions=[genesis_transaction.to_dict()],
                validator=self.wallet.public_key,
                previous_hash="1"
            )
            self.blockchain.add_block(genesis_block)

    def update_blockchain(self, incoming_chain):
        try:
            # Temporarily save the current blockchain
            current_chain_backup = self.blockchain.chain

            # Convert the incoming chain data into Block instances and set it as the current blockchain chain for validation
            self.blockchain.chain = [Block(**block_data) for block_data in incoming_chain]

            # Validate the temporarily set incoming chain
            if self.blockchain.validate_chain():
                current_len = len(current_chain_backup)
                incoming_len = len(self.blockchain.chain)

                # Check if the incoming chain is longer than the current chain
                if incoming_len > current_len:
                    # The incoming chain is valid and longer, keep it as the new chain
                    print(f"Blockchain updated with a longer chain of length {incoming_len}.")
                    return True
                else:
                    # The incoming chain is valid but not longer, restore the original chain
                    self.blockchain.chain = current_chain_backup
                    print("Received chain is not longer than the current chain.")
            else:
                # The incoming chain is invalid, restore the original chain
                self.blockchain.chain = current_chain_backup
                print("Received chain is invalid.")

            return False
        except Exception as e:
            print(f"An error occurred during blockchain update: {e}")
            self.blockchain.chain = current_chain_backup  # Restore the original chain in case of error
            return False
        

    def register_with_bootstrap(self, bootstrap_url, public_key):
        response = requests.post(bootstrap_url + '/register', json={'public_key': public_key, 'node_address': self.api_url})
        if response.status_code == 200:
            data = response.json()
            if 'node_address' in data:
                self.update_blockchain(data['blockchain'])
                for node_id, node_info in data['nodes'].items():
                    if node_id == '4':
                        self.nodes = data['nodes']
                print('Registered with the bootstrap node')
                print('Local blockchain initialized with the received state from the bootstrap node')
            else:
                print('Error: node_address not found in the response.')
                return False
        else:
            return False

    def transfer_bcc_to_new_node(self, recipient_public_key, amount):
        """
        Create and execute a transaction to transfer BCC from this node to a new node,
        then mint a new block containing this transaction.
        """

        sender_address = self.wallet.public_key  
        receiver_address = recipient_public_key  
        amount = amount    
        nonce = self.get_next_nonce()  

        # Create a Transaction object with extracted fields
        transaction = Transaction(sender_address, receiver_address, "Welcome!", amount, "", nonce)
           
        transaction.sign_transaction(self.wallet.private_key)
        # Add the signed transaction to the transaction pool
        self.blockchain.add_transaction_to_pool(transaction)
    
        temptrans = Transaction(receiver_address, 0, "Welcome!", 10, "", 1)

        temptrans.sign_transaction(self.wallet.private_key)

        self.blockchain.add_transaction_to_pool(temptrans)

        # Mint a new block containing this transaction (PoS-specific logic may apply here)
        self.blockchain.mint_bootstrap_block(self.wallet.public_key)  # Use bootstrap node's public key as the validator


    def get_node_id_by_public_key(self, public_key):
        # print("Searching for public_key:", public_key)
        # Iterate over the dictionary items
        for node_id, node_info in self.nodes.items():
            # print("Comparing with node:", node_id, node_info)
            if node_info["public_key"] == public_key:
                print("Match found! Node ID:", node_id)
                return node_id  # Return the key (node ID)
        print("No match found.")
        return None

    def get_next_nonce(self):

        # Start by considering transactions in the blockchain
        max_nonce = 0
        for block in self.blockchain.chain:
            for transaction in block.transactions:

                if isinstance(transaction, Transaction):
                    sender_address = transaction.sender_address
                    if sender_address == self.wallet.address:
                        max_nonce = max(max_nonce, transaction.nonce)
                elif isinstance(transaction, dict):
                    sender_address = transaction['sender_address']
                    if sender_address == self.wallet.address:
                        max_nonce = max(max_nonce, transaction['nonce'])
                else:
                    raise TypeError("Unexpected transaction type")

        # Also consider transactions in the transaction pool
        for transaction in self.blockchain.transaction_pool:

            if isinstance(transaction, Transaction):
                sender_address = transaction.sender_address
                if sender_address == self.wallet.address:
                    max_nonce = max(max_nonce, transaction.nonce)
            elif isinstance(transaction, dict):
                sender_address = transaction['sender_address']
                if sender_address == self.wallet.address:
                    max_nonce = max(max_nonce, transaction['nonce'])
            else:
                raise TypeError("Unexpected transaction type")
            

        # The next nonce should be one more than the max found
        return max_nonce + 1



    def stake(self, amount):
        """
        Set the stake amount for the node.
        """
        if amount < 0:
            return False, "Stake amount cannot be negative"
        
        temptrans = Transaction(self.wallet.public_key, "stake", 0, "coins", amount,"",1)
        temptrans.sign_transaction(self.wallet.private_key)
        self.broadcast_transaction(temptrans)
        return True, "Stake amount set successfully"
    
    def PoS_Choose_Minter(self,seed):

        seed_hash = hashlib.sha256(seed.encode()).hexdigest()
        seed_int = int(seed_hash, 16)

        total_stakes = 0
        for node_id, node_info in self.nodes.items():
            total_stakes+= self.calculate_stakes(self.blockchain.chain, node_info['public_key'])
        rng = numpy.random.default_rng(seed_int)
        if total_stakes == 0:
            return False 

        stake_target = rng.uniform(0, total_stakes)
        current = 0

        for node_id, node_info in self.nodes.items():
            current += self.calculate_stakes(self.blockchain.chain, node_info['public_key'])
            if current >= stake_target:
                validator = node_info['public_key']
                break
        return validator

    def validate_block(self, block):
        """
        Validate a block by checking the validator and previous hash.
        """
        # # Check if the validator matches the stakeholder
        if block.validator != self.PoS_Choose_Minter(block.previous_hash):
            return False, "Block Validator does not match the result of the pseudo-random generator"

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
        sender_address = transaction.sender_address    
        amount = transaction.amount

        # Verify the transaction signature
        if not transaction.verify_signature():
            return False, "Invalid signature"

        if transaction.type_of_transaction == "coin":
            if self.calculate_balance(self.blockchain.chain, sender_address) - self.calculate_stakes(self.blockchain.chain, sender_address) < 1.03*amount:
                return False, "Insufficient balance"
            return True, "Transaction validated successfully"
        elif transaction.type_of_transaction == "message":
            if self.calculate_balance(self.blockchain.chain, sender_address) - self.calculate_stakes(self.blockchain.chain, sender_address) < len(transaction.message):
                return False, "Insufficient balance"
            return True, "Transaction validated successfully"
        elif transaction.type_of_transaction == "Welcome to the network!":
            return True, "Bootstrap Transaction"
        else:
            return False, "Unknown Transaction type"


    def broadcast_transaction(self, transaction):
        for node_id, node_info in self.nodes.items():
            node_url = node_info['address'] 
            requests.post(node_url + '/transactions/new', json=transaction.to_dict())
        print('Transaction broadcasted to the network')

    def broadcast_block(self, block):
        for node_id, node_info in self.nodes.items():
            node_url = node_info['address'] 
            requests.post(node_url + '/receive_block', json=block.to_dict())
        print('Block broadcasted to the network')

    def validate_chain(self, chain):
        """
        Validate the received blockchain by validating each block in it.
        """
        for block in self.blockchain.chain[1:]:  # Exclude the genesis block
            is_valid, message = self.validate_block(block)
            if not is_valid:
                return False, f"Blockchain validation failed: {message}"

        return True, "Blockchain validation successful"

    def broadcast_all(self):
        # Data to be broadcasted: IP address, port, and public keys of all nodes
        data_to_broadcast = {
            node_id: {
                'address': node_info['address'],
                'public_key': node_info['public_key']
            }
            for node_id, node_info in self.nodes.items()
        }
        try:
            self.send_data(data_to_broadcast)
        except Exception as e:
            print(f"Failed to send data")

        print("Broadcast completed to all nodes in the network.")

    def send_data(self, data):
        for node_id, node_info in self.nodes.items():
            if node_id == self.node_id:
                continue
            ip_address = node_info['address']
            url = f"{ip_address}/receive_data"

            try:
                response = requests.post(url, json=data)
                if response.status_code == 200:
                    print(f"Data successfully sent to node {node_id}.")
                else:
                    print(f"Failed to send data to node {node_id}. Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to send data to node {node_id}: {e}")

    def view(self):
        """
        View last transactions: print the transactions contained in the last validated block
        of the BlockChat blockchain.
        """
        last_block = self.blockchain.get_last_block()
        if last_block:
            transactions = last_block.transactions
            val_id = self.get_node_id_by_public_key(last_block.validator)
            print(f"Validator id:{val_id}")
            print("Last transactions:")
            for transaction in transactions:
                print(transaction)
        else:
            print("Blockchain is empty or not synchronized.")


    def create_transaction(self, recipient_address, amount, message="", type_of_transaction="coin"):
        """
        Send a transaction to the recipient address with the specified amount.
        """

        # Validate recipient address and amount (you may need additional validation logic here)
        if not recipient_address:
            print("Recipient address is required.")
            return

        try:
            amount = float(amount)
        except ValueError:
            print("Invalid amount. Please enter a numeric value.")
            return

        # Find the recipient's public key using the recipient_address
        recipient_public_key = None
        for node_id, node_info in self.nodes.items():
            if node_info['address'] == recipient_address:
                recipient_public_key = node_info['public_key']
                break

        # Create a transaction object
        transaction = Transaction(
            sender_address=self.wallet.public_key,
            receiver_address=recipient_public_key,
            amount=float(amount),
            type_of_transaction=type_of_transaction,  # Specify the transaction type here
            message=message,
            nonce=self.get_next_nonce()  # Assuming a method to manage nonce
        )

        transaction.sign_transaction(self.wallet.private_key)

        # Validate the transaction
        is_valid, message = self.validate_transaction(transaction)
        if not is_valid:
            print(f"Transaction validation failed: {message}")
            return False
        else: 
            # Broadcast the transaction to the network
            self.broadcast_transaction(transaction)
            print("Transaction sent successfully.")
            return True


    def mint_block(self):
        currentValidator = self.PoS_Choose_Minter(self.blockchain.chain[-1].current_hash)
        if self.wallet.public_key == currentValidator:
            # Only create a new block if there are transactions in the pool
            if len(self.blockchain.transaction_pool) >= self.blockchain.block_capacity:
                previous_block = self.blockchain.chain[-1]
                new_block = Block(index=len(self.blockchain.chain), transactions=self.blockchain.transaction_pool, validator=currentValidator, previous_hash=previous_block.current_hash)
                new_block.current_hash = new_block.calculate_hash()
                if self.blockchain.add_block(new_block):
                    print("Block added")
                else:
                    print("Block not added")
                if self.broadcast_block(new_block):
                    print("Block broadcasted")
                else:
                    print("Block didnt broadcast")
                    self.blockchain.transaction_pool = self.blockchain.transaction_pool[self.blockchain.block_capacity:]  
                print("Block added to the chain")
            else:
                print("Transaction pool not full")


    def calculate_balance(self, blockchain, public_key):
        balance = 0
        for block in blockchain:
            for transaction in block.transactions:
                # Check if the wallet is the recipient
                if transaction['receiver_address'] == public_key:
                    balance += transaction['amount']
                # Check if the wallet is the sender
                if transaction['sender_address'] == public_key and transaction['receiver_address'] != 0:
                    if transaction['type_of_transaction'] == "Welcome!":
                        balance = transaction['amount']
                    elif transaction['type_of_transaction'] == "coin":
                        balance -= 1.03*transaction['amount'] 
                    else:    
                        balance -= len(transaction['message'])
                
        return balance

    def calculate_stakes(self, blockchain, public_key):
        totstake = 0
        for block in blockchain:
            for transaction in block.transactions:
                # Check if the wallet is the recipient
                if transaction['receiver_address'] == 0 and transaction['sender_address'] == public_key: 
                    totstake += transaction['amount']
        return totstake
    
        