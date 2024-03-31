import random

from flask.json import jsonify
from block import Block

import time
import hashlib

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transaction_pool = []
        self.stakes = []
        self.validatorHistory = []
    
    def add_transaction_to_pool(self, transaction):
        self.transaction_pool.append(transaction)
        print('Transaction added to pool')
        return
    
    def mint_block(self):
        # Only create a new block if there are transactions in the pool
        if len(self.transaction_pool) > 0:
            previous_block = self.chain[-1]
            previous_hash = previous_block.current_hash if previous_block else "0"
            currentValidator = self.PoS_Choose_Minter
            new_block = Block(index=len(self.chain), transactions=self.transaction_pool, validator=currentValidator, previous_hash=previous_block.current_hash)
            new_block.current_hash = new_block.calculate_hash()
            self.add_block(new_block)
            self.validatorHistory[new_block.index] = currentValidator
            self.transaction_pool = []  # Clear the transaction pool after adding to the block CAREFUL MAYBE THERE WERE SOME MORE THAT DIDNT FIT?
            print("Block added to the chain")
        else:
            print("No transactions to add")

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
        self.blockCounter += 1
        return jsonify({"message": "New block added"}), 200
        #print(f"Block {block.index} added to the chain")
        
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
            
            if current_block.calculate_hash() != current_block.current_hash:
                print("Block hash calculation mismatch at Block", current_block.index)
                return False
        
        print("Blockchain is valid.")
        return True

    def PoS_Choose_Minter(self):
        """
        Validate the block by selecting a validator based on their stake.
        """

        total_stakes = sum(self.stakes.values())
        if total_stakes == 0:
            return False 

        stake_target = random.uniform(0, total_stakes)
        current = 0
        for node_identifier, stake_amount in self.stakes.items():
            current += stake_amount
            if current >= stake_target:
                validator = node_identifier
                break
        return validator
    
    def get_last_block(self):
        """
        Retrieve the last block in the blockchain.
        """
        if self.chain:
            return self.chain[-1]
        else:
            return None
    
# Example usage
if __name__ == "__main__":
    blockchain = Blockchain()
    blockchain.add_block(transactions=[{"from": "Alice", "to": "Bob", "amount": 50}], validator="Validator1")
    blockchain.validate_chain()