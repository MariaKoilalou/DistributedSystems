from block import Block

import time
import hashlib

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transaction_pool = []

    # To evala sto node.py
    # def create_genesis_block(self):
    #     """
    #     Create the first block in the blockchain, known as the Genesis Block.
    #     """
    #     genesis_block = Block(index=0, transactions=[], validator="GenesisBlockValidator", previous_hash="0")
    #     genesis_block.current_hash = genesis_block.calculate_hash()
    #     self.chain.append(genesis_block)
    
    def add_transaction_to_pool(self, transaction):
        self.transaction_pool.append(transaction)
        print('Transaction added to pool')
        return
    
    def add_block(self, validator):
        # Only create a new block if there are transactions in the pool
        if len(self.transaction_pool) > 0:
            previous_block = self.chain[-1]
            new_block = Block(index=len(self.chain), transactions=self.transaction_pool, validator=validator, previous_hash=previous_block.current_hash)
            new_block.current_hash = new_block.calculate_hash()
            self.chain.append(new_block)
            self.transaction_pool = []  # Clear the transaction pool after adding to the block
            print("Block added to the chain")
        else:
            print("No transactions to add")

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

    def PoS_Choose_Minter(self, block):
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
    
# Example usage
if __name__ == "__main__":
    blockchain = Blockchain()
    blockchain.add_block(transactions=[{"from": "Alice", "to": "Bob", "amount": 50}], validator="Validator1")
    blockchain.validate_chain()
