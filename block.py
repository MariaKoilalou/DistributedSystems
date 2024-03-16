import time
import hashlib
import json

class Block:
    def __init__(self, index, transactions, validator, previous_hash, capacity=3):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions[:capacity]  # Limit transactions to capacity
        self.validator = validator
        self.previous_hash = previous_hash
        self.current_hash = self.calculate_hash()
        self.capacity = capacity

    def calculate_hash(self):
        """
        Calculate the hash of the block by hashing the concatenation of the block's main components.
        """
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.transactions)}{self.validator}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        """
        Convert the block details into a dictionary for easier processing and transmission.
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'validator': self.validator,
            'previous_hash': self.previous_hash,
            'current_hash': self.current_hash,
            'capacity': self.capacity
        }


    def __repr__(self):
        return f"Block(Index: {self.index}, Hash: {self.current_hash}, Prev Hash: {self.previous_hash}, Transactions: {len(self.transactions)})"

# Example usage
if __name__ == "__main__":
    # Example transactions and validator
    transactions = [{"sender": "Alice", "recipient": "Bob", "amount": 100}]
    validator = "ValidatorPublicKey"

    # Creating a genesis block
    genesis_block = Block(0, transactions, validator, "0")
    print(genesis_block)

    # Adding another block
    second_block = Block(1, transactions, validator, genesis_block.current_hash)
    print(second_block)
