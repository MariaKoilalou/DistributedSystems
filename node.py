import requests
import json

from wallet import Wallet
from blockchain import Blockchain
from transaction import Transaction
from block import Block



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
                nonce=0,
                message="Genesis Block"
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
            # Check if 'node_address' key exists in the response
            if 'node_address' in data and 'blockchain' in data:
                self.nodes[data['node_id']] = data['node_address']
                print('Registered with the bootstrap node')
                # Initialize the local blockchain with the received state
                received_chain = data['blockchain']
                # Assuming you have a method to replace the current blockchain with a new one
                self.update_blockchain(received_chain)
                print('Local blockchain initialized with the received state from the bootstrap node')
                return True
            else:
                # Handle the case where 'node_address' is not present
                print('Error: node_address not found in the response.')
                return False
        return False

    

    def register_node(self, public_key, node_address):
        """Register a new node in the network, assign it a unique ID, and transfer 1000 BCC to it."""
        if not self.is_bootstrap:
            print("This node is not the bootstrap node.")
            return False, None
        
        node_id = len(self.nodes) + 1
        self.nodes[public_key] = {"id": node_id, "address": node_address}
        print(f"Node {node_id} registered with public key {public_key}.")

        # Transfer 1000 BCC from the bootstrap node to the new node
        self.transfer_bcc_to_new_node(public_key, 1000)

        # # After registering the new node, broadcast the updated nodes and blockchain to all nodes
        self.broadcast_blockchain(node_address)

        print(f"Node {node_id} registered with public key {public_key}.")

        return True, node_id


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

        # Extract necessary fields from signed_transaction
        sender_address = self.wallet.public_key  # Sender address is the public key of the wallet
        receiver_address = recipient_public_key  # Assign recipient address directly
        amount = signed_transaction['amount']  # Extract amount from signed transaction
        message = signed_transaction['message']  # Extract message from signed transaction
        nonce = signed_transaction['nonce']  # Extract nonce from signed transaction

        # Create a Transaction object with extracted fields
        transaction = Transaction(sender_address, receiver_address, "regular", amount, message, nonce)

        transaction = transaction.to_dict()

        self.blockchain.add_transaction_to_pool(transaction)

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
        for block in self.blockchain.chain[1:]:  # Exclude the genesis block
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

        for _, node_info in self.nodes.items():
            node_url = node_info['address']
            try:
                response = requests.get(f'{node_url}/blockchain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    # Convert the received chain data into Block instances
                    formatted_chain = [Block(**block_data) for block_data in chain]

                    # Check if the formatted chain is longer and valid
                    if length > current_len and self.blockchain.validate_chain(formatted_chain):
                        current_len = length
                        longest_chain = formatted_chain
            except Exception as e:
                print(f"Error fetching blockchain from {node_url}: {e}")

        if longest_chain:
            # Update the blockchain of all nodes with the longest valid chain found
            for _, node_info in self.nodes.items():
                node_info['blockchain'].chain = longest_chain
            return True
        return False


    def view(self):
        """
        View last transactions: print the transactions contained in the last validated block
        of the BlockChat blockchain.
        """
        last_block = self.blockchain.get_last_block()
        if last_block:
            transactions = last_block.transactions
            print("Last transactions:")
            for transaction in transactions:
                print(transaction)
        else:
            print("Blockchain is empty or not synchronized.")

    def sendTransCli(self, recipient_address, amount):
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

        # Create a transaction object
        transaction = Transaction(
            sender_address=self.wallet.public_key,
            receiver_address=recipient_address,
            amount=float(amount),
            type_of_transaction="regular",  # Specify the transaction type here
            message="Transaction message",
            nonce=self.get_next_nonce()  # Assuming a method to manage nonce
        )

        # Validate the transaction
        is_valid, message = self.validate_transaction(transaction)
        if not is_valid:
            print(f"Transaction validation failed: {message}")
            return

        # Broadcast the transaction to the network
        self.broadcast_transaction(transaction)
        print("Transaction sent successfully.")

    def broadcast_blockchain(self):
        if self.is_bootstrap:
            # Broadcast the current blockchain to all registered nodes
            blockchain_data = {
                'chain': [block.to_dict() for block in self.blockchain.chain],
                'length': len(self.blockchain.chain),
            }

            for _, node_info in self.nodes.items():
                node_address = node_info['address']
                try:
                    response = requests.post(f"{node_address}/update_blockchain", json=blockchain_data)
                    if response.status_code != 200:
                        print(f"Failed to broadcast blockchain to {node_address}. Response code: {response.status_code}")
                    else :
                        print(f"Successfully broadcasted blockchain to {node_address}.")
                except requests.exceptions.RequestException as e:
                    print(f"Error broadcasting blockchain to {node_address}: {e}")
                
    
