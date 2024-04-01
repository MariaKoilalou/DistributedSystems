import time
import hashlib
import json

class Block:
    def __init__(self, index, transactions, validator, previous_hash, capacity=3, timestamp=None, current_hash=None):
        self.index = index
        self.timestamp = round(timestamp if timestamp is not None else time.time(), 4)
        self.transactions = transactions[:capacity]  # Limit transactions to capacity
        self.validator = validator
        self.previous_hash = previous_hash
        self.capacity = capacity
        self.current_hash = current_hash if current_hash is not None else self.calculate_hash()

    def serialize_for_hash(self):
        # Serialize block data in a consistent order
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'validator': self.validator,
            'previous_hash': self.previous_hash
        }
        return json.dumps(block_data, sort_keys=True)
    
    def calculate_hash(self):
        # Use serialized block data for hash calculation
        block_string = self.serialize_for_hash()
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

