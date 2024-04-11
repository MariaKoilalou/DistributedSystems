import hashlib
import json
import os
import time
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
        self.total_transactions = 0
        self.throughput = 0
        longest_processing_time = 0
        self.block_count = 0
        self.block_count = 0
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
                previous_hash="1",
                capacity=self.blockchain.block_capacity
            )
            self.blockchain.add_block(genesis_block)
            temptrans = Transaction(self.wallet.public_key, 0, "Initial stake", 10, "", 1)

            temptrans.sign_transaction(self.wallet.private_key)

            self.blockchain.add_transaction_to_pool(temptrans.to_dict())

            self.blockchain.mint_bootstrap_block(self.wallet.public_key) 

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
                self.blockchain.transaction_pool = data['transaction_pool']
                
                temptrans = Transaction(self.wallet.public_key, 0, "Initial stake", 10, "", 1)

                temptrans.sign_transaction(self.wallet.private_key)

                self.blockchain.add_transaction_to_pool(temptrans.to_dict())

                for node_id, node_info in data['nodes'].items():
                    if node_id == "0":
                        bootstrap_key = node_info['public_key']

                # self.blockchain.mint_bootstrap_block(bootstrap_key) 

                if self.validate_chain:
                    print('Local blockchain initialized with the received state from the bootstrap node')
                else:
                    print("Invalid chain")
                    return False
                
                for node_id, node_info in data['nodes'].items():
                    if node_id == str(self.total_nodes-1):
                        self.nodes = data['nodes']
                print('Registered with the bootstrap node')
                return True
            else:
                print('Error: node_address not found in the response.')
                return False
        else:
            return False



    def transfer_bcc_to_new_node(self, recipient_public_key, amount):

        sender_address = self.wallet.public_key  
        receiver_address = recipient_public_key  
        amount = amount    
        nonce = self.get_next_nonce()  

        # Create a Transaction object with extracted fields
        transaction = Transaction(sender_address, receiver_address, "Welcome!", amount, "", nonce)
           
        transaction.sign_transaction(self.wallet.private_key)
        # Add the signed transaction to the transaction pool
        self.blockchain.add_transaction_to_pool(transaction.to_dict())
    
        self.blockchain.mint_bootstrap_block(self.wallet.public_key)



    def get_node_id_by_public_key(self, public_key):
        for node_id, node_info in self.nodes.items():
            if node_info['public_key'] == public_key:
                print("Match found! Node ID:", node_id)
                return node_id 
        print("No match found.")
        return None
    

    def get_next_nonce(self):
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

        for transaction in self.blockchain.transaction_pool:
            if isinstance(transaction, Transaction):
                sender_address = transaction.sender_address
                if sender_address == self.wallet.address:
                    max_nonce = max(max_nonce, transaction.nonce)
            elif isinstance(transaction, dict):
                sender_address = transaction['sender_address']
                if sender_address == self.wallet.address:
                    max_nonce = max(max_nonce, transaction['nonce'])
        return max_nonce + 1

    def stake(self, amount):
        if amount < 0:
            return False, "Stake amount cannot be negative"
        
        transaction = {
            'sender_address': self.wallet.public_key,
            'receiver_address':0,
            'amount': amount,
            'type_of_transaction' : "stake",  
            'message': "",
            'nonce': 1,
            'private_key': self.wallet.private_key
        }

        self.broadcast_transaction(transaction)

    
    def PoS_Choose_Minter(self,seed):

        seed_hash = hashlib.sha256(seed.encode()).hexdigest()
        seed_int = int(seed_hash, 16)

        total_stakes = 0
        for node_id, node_info in self.nodes.items():
            total_stakes+= self.calculate_stakes(node_info['public_key'])
        rng = numpy.random.default_rng(seed_int)
        if total_stakes == 0:
            return False 

        stake_target = rng.uniform(0, total_stakes)
        current = 0

        for node_id, node_info in self.nodes.items():
            current += self.calculate_stakes(node_info['public_key'])
            if current >= stake_target:
                validator = node_info['public_key']
                break
        return validator

    def validate_block(self, block):
        # Check if the validator matches the stakeholder
        if block.validator != self.PoS_Choose_Minter(block.previous_hash):
            return False, "Block Validator does not match the result of the pseudo-random generator"

        # Retrieve the previous block from the blockchain
        previous_block = self.blockchain.chain[-1]

        # Check if the previous hash in the block matches the hash of the previous block
        if block.previous_hash != previous_block.current_hash:
            return False, "Invalid previous hash"

        return True, "Block validated successfully"
    

    def validate_transaction(self, transaction):
        sender_address = transaction.sender_address    
        amount = transaction.amount

        # Verify the transaction signature
        if not transaction.verify_signature():
            return False

        if transaction.type_of_transaction == "coin":
            if self.calculate_balance(sender_address) - self.calculate_stakes(sender_address) < 1.03*amount:
                print("Insufficient balance")
                return False
            return True, "Transaction validated successfully"
        elif transaction.type_of_transaction == "message":
            if self.calculate_balance(sender_address) - self.calculate_stakes(sender_address) < len(transaction.message):
                print("Insufficient balance")
                return False
            print("Transaction validated successfully")
            return True
        elif transaction.type_of_transaction == "Welcome!" or transaction.type_of_transaction == "genesis" or transaction.type_of_transaction == "Initial stake":
            print("Bootstrap Transaction")
            return True
        elif transaction.type_of_transaction == "stake":
            if self.calculate_balance(sender_address) - self.calculate_stakes(sender_address) < amount:
                print("Stake too much")
                return False
            print("Stake Transaction")
            return True
        else:
            print("Unknown Transaction type")
            return False


    def broadcast_transaction(self, transaction):
        for node_id, node_info in self.nodes.items():
            node_url = node_info['address'] 
            requests.post(node_url + '/transactions/new', json=transaction)

    def broadcast_block(self, block):
        for node_id, node_info in self.nodes.items():
            node_url = node_info['address'] 
            requests.post(node_url + '/receive_block', json=block)
        print('Block broadcasted to the network')

    def validate_chain(self):
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
        node_items = list(self.nodes.items())[:-1]
        
        for node_id, node_info in node_items:
        
            # Skip sending data if the current node is the node itself
            if node_id == self.node_id:
                continue
            if node_id == self.total_nodes - 1:
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
        last_block = self.blockchain.chain[-1]
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


        transaction = {
            'sender_address': self.wallet.public_key,
            'receiver_address': recipient_public_key,
            'amount': float(amount),
            'type_of_transaction' : type_of_transaction,  
            'message': message,
            'nonce': self.get_next_nonce(),
            'private_key': self.wallet.private_key
        }

        self.broadcast_transaction(transaction)

        return True
            


    def mint_block(self):
            currentValidator = self.PoS_Choose_Minter(self.blockchain.chain[-1].current_hash)
            if len(self.blockchain.transaction_pool) == self.blockchain.block_capacity:
                transactions = self.blockchain.transaction_pool
                self.blockchain.transaction_pool = []
                if self.wallet.public_key == currentValidator:
                        previous_block = self.blockchain.chain[-1]

                        # Handle both dict and Transaction instances in the transaction pool
                        transactions_data = []
                        for tx in transactions:
                            if isinstance(tx, Transaction):
                                transactions_data.append(tx.to_dict())
                            elif isinstance(tx, dict):
                                transactions_data.append(tx)  # tx is already a dict
                            else:
                                print("Unsupported transaction type in transaction pool")
                                continue

                        new_block_data = {
                            'index': len(self.blockchain.chain),
                            'transactions': transactions_data,
                            'validator': currentValidator,
                            'previous_hash': previous_block.current_hash
                        }

                        try: 
                            self.broadcast_block(new_block_data)
                            print("Block broadcasted")
                        except Exception as e:
                            print(f"Broadcast block failed: {e}")
                            return False
            else:
                print("Transaction pool not full")






    def calculate_balance(self, public_key):
        balance = 0

        for block in self.blockchain.chain:
            for transaction in block.transactions:
                if transaction['receiver_address'] == public_key :
                    balance += transaction['amount']
                if transaction['sender_address'] == public_key and transaction['receiver_address'] != 0 and balance > 0 :
                    if transaction['type_of_transaction'] == "Welcome!":
                        balance -= transaction['amount']
                    elif transaction['type_of_transaction'] == "coin":
                        balance -= 1.03*transaction['amount'] 
                    elif transaction['type_of_transaction'] == "message":    
                        balance -= len(transaction['message'])

        for transaction in self.blockchain.transaction_pool:
                if transaction['receiver_address'] == public_key :
                    balance += transaction['amount']
                if transaction['sender_address'] == public_key and transaction['receiver_address'] != 0 and balance > 0:
                    if transaction['type_of_transaction'] == "Welcome!":
                        balance -= transaction['amount']
                    elif transaction['type_of_transaction'] == "coin":
                        balance -= 1.03*transaction['amount'] 
                    elif transaction['type_of_transaction'] == "message":    
                        balance -= len(transaction['message'])

        if balance > 0:
            return balance
        else:
            balance = 0 
            return balance

    def calculate_stakes(self, public_key):
        totstake = 10

        for transaction in reversed(self.blockchain.transaction_pool):
            if transaction['type_of_transaction'] == "stake" and transaction['sender_address'] == public_key:
                totstake = transaction['amount']
                break  

        if totstake == 10: 
            for block in reversed(self.blockchain.chain):  
                for transaction in reversed(block.transactions):  
                    if transaction['type_of_transaction'] == "stake" and transaction['sender_address'] == public_key:
                        totstake = transaction['amount']
                        return totstake  

        return totstake

    def start_test_all_nodes(self, node_addresses, transactions_folder):
        for node_address in node_addresses:
            try:
                response = requests.post(node_address + '/start_test', json={'transactions_folder': transactions_folder})
                if response.status_code == 200:
                    print(f"Transaction test started successfully at {node_address}")
                else:
                    print(f"Failed to start transaction test at {node_address}. Status Code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error communicating with node at {node_address}: {e}")


    def start_transaction_test(self, transactions_folder, node_id): 
        self.node_id = node_id
        transactions_file_path = os.path.join(transactions_folder, f'trans{node_id}.txt')
        if not os.path.exists(transactions_file_path):
            print(f"Transaction file '{transactions_file_path}' does not exist.")
            return
        self.load_and_process_transactions(transactions_file_path)

    def load_and_process_transactions(self, filepath):
        with open(filepath, 'r') as file:
            start_time = time.time()
            transaction_count = 0
            node_transactions = 0
            for line in file:
                parts = line.strip().split(' ', 1)
                if len(parts) != 2:
                    print("Invalid transaction format in file:", line)
                    continue

                node_id_part, message = parts
                recipient_id = ''.join(filter(str.isdigit, node_id_part))
                if not recipient_id:
                    print(f"Could not extract recipient ID from: {node_id_part}")
                    continue

                recipient_id = str(recipient_id) 

                for node_id, node_info in self.nodes.items():
                    node_id = str(node_id).strip()  
                    if node_id == recipient_id:
                        recipient_info = node_info
                        break
                else:
                    print(f"Recipient node ID {recipient_id} not found in nodes dictionary.")
                    continue

                recipient_address = recipient_info['address']

                self.create_transaction(recipient_address, 0, message, "message")

                transaction_count += 1

            end_time = time.time()
            processing_time = end_time - start_time
            node_transactions += transaction_count

            metrics_filepath = f'metrics_{self.total_nodes}_nodes_capacity{self.blockchain.block_capacity}_for_node{self.node_id}.txt'
            self.save_metrics(metrics_filepath, processing_time, node_transactions)


    def count_blocks(self):
        if not self.blockchain.chain:
            print("Blockchain chain is empty.")
            return 0
        else:
            block_count = len(self.blockchain.chain)
            print(f"Blockchain contains {block_count} blocks.")
            return block_count

    
    def save_metrics(self, metrics_filename, processing_time, node_transactions):
        if node_transactions == 0:
            print("No transactions to calculate metrics.")
            return

        # block_count = self.count_blocks()  
        throughput = node_transactions / processing_time if processing_time > 0 else 0
        # block_time = self.total_processing_time / block_count if block_count else 0

        current_directory = os.getcwd()  # Get the current working directory
        directory_path = os.path.join(current_directory, 'test_results')  # Form the path to the test_results directory
        filepath = os.path.join(directory_path, metrics_filename)  # Form the full file path
        
        # Ensure the directory exists
        os.makedirs(directory_path, exist_ok=True)  # Create the directory if it does not exist
        
        # Write the metrics to the file
        try:
            with open(filepath, 'w') as file:
                file.write(f"Transactions: {node_transactions}\n")
                file.write(f"Throughput: {throughput} transactions/second\n")
                # file.write(f"Block Count: {block_count}\n")
                # file.write(f"Average Block Time: {block_time} seconds/block\n")
        except Exception as e:
            print(f"Failed to save metrics: {e}")

        self.aggregate_metrics(total_nodes = self.total_nodes, folder_path='test_results/', output_filename=f'metrics_{self.total_nodes}_nodes_capacity{self.blockchain.block_capacity}.txt')

    def aggregate_metrics(self, total_nodes, folder_path, output_filename):
    
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        # Check if the number of metric files matches the total number of nodes
        if len(files) == total_nodes:
            longest_processing_time = 0
            self.total_transactions=0
            self.throughput=0
            self.block_count=0
            self.block_time=0
            # Iterate through each file and aggregate the metrics
            for file in files:
                with open(os.path.join(folder_path, file), 'r') as f:
                    for line in f:
                        if "Transactions" in line:
                            self.total_transactions += int(line.split(":")[1].strip())
                        elif "Throughput" in line:
                            processing_time = float(line.split(":")[1].strip().split()[0])  
                            longest_processing_time = max(longest_processing_time, processing_time)
  
            # Calculate new aggregated metrics
            self.throughput = self.total_transactions / longest_processing_time if longest_processing_time > 0 else 0
            self.block_count = self.count_blocks()  
            self.block_time = processing_time / self.block_count if self.block_count else 0

            output_filepath = os.path.join(folder_path, output_filename)
            with open(output_filepath, 'w') as output_file:
                output_file.write(f"Total Transactions: {self.total_transactions}\n")
                output_file.write(f"Total Throughput: {self.throughput} transactions/second\n")
                output_file.write(f"Total Block Count: {self.block_count}\n")
                output_file.write(f"Average Block Time: {self.block_time} seconds/block\n")
            
            print(f"Aggregated metrics saved to {output_filepath}")

    def take_metrics(self):
        print(f"Total Transactions: {self.total_transactions}\n")
        print(f"Total Throughput: {self.throughput} transactions/second\n")
        print(f"Total Block Count: {self.block_count}\n")
        print(f"Average Block Time: {self.block_time} seconds/block\n")

