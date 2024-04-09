import random

from flask.json import jsonify
from block import Block

import time
import hashlib

class Blockchain:
    def __init__(self, block_capacity=5):
        self.chain = []
        self.transaction_pool = []
        self.stakes = {} 
        self.block_capacity = block_capacity
    
    def add_transaction_to_pool(self, transaction):
        self.transaction_pool.append(transaction)
        print('Transaction added to pool')
        return
    
    def mint_bootstrap_block(self, validator):
        # Only create a new block if there are transactions in the pool
        if len(self.transaction_pool) == self.block_capacity:
            previous_block = self.chain[-1]
            new_block = Block(index=len(self.chain), transactions=self.transaction_pool, validator=validator, previous_hash=previous_block.current_hash)
            new_block.current_hash = new_block.calculate_hash()
            self.add_block(new_block)
            self.transaction_pool = []
            print("Block added to the chain")
        else:
            print("Transaction pool not full")



    def add_block(self, block):
        """
        Add a new block to the blockchain.
        
        :param block: The block to be added.
        """
        # If it's the first block and the chain is empty, it's considered the Genesis block
        if not self.chain:
            if block.index != 0:
                raise Exception("The first block must be the Genesis block with index 0")
        else:
            # Ensure the new block follows the last block on the chain
            if block.previous_hash != self.chain[-1].current_hash:
                raise Exception("The new block's previous hash must match the last block's hash")

        self.chain.append(block)
        print("New block added, current blockchain state:", self.chain)
        return "New block added", 200
        
    def validate_chain(self):
        """
        Validate the current blockchain to ensure integrity.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.previous_hash != previous_block.current_hash:
                print("Blockchain integrity compromised at Block", current_block.index)
                return False
            
            recalculated_hash = hashlib.sha256(current_block.serialize_for_hash().encode()).hexdigest()
            if recalculated_hash != current_block.current_hash:
                print("Block hash calculation mismatch at Block", current_block.index)
                return False

        print("Blockchain is valid.")
        return True

    
