import time
import hashlib
import json

class Block:
    def __init__(self, index, transactions, validator, previous_hash, capacity=5, timestamp=None, current_hash=None):
        self.index = index
        self.start_time = time.time()  # Record when block creation starts
        self.timestamp = round(timestamp if timestamp is not None else time.time(), 4)
        self.transactions = transactions[:capacity]  # Limit transactions to capacity
        self.validator = validator
        self.previous_hash = previous_hash
        self.capacity = capacity
        self.current_hash = current_hash if current_hash is not None else self.calculate_hash()
        self.end_time = time.time()  # Record when block creation ends

    def block_creation_time(self):
        return self.end_time - self.start_time
    
    def serialize_for_hash(self):
        # Serialize block data in a consistent order
        block_data = {
            'index': self.index,
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in self.transactions],            
            'validator': self.validator,
            'previous_hash': self.previous_hash
        }
        return json.dumps(block_data, sort_keys=True)
    
    def calculate_hash(self):
        # Use serialized block data for hash calculation
        block_string = self.serialize_for_hash()
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self):
         
        transactions_dict_list = [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in self.transactions]

        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': transactions_dict_list,
            'validator': self.validator,
            'previous_hash': self.previous_hash,
            'current_hash': self.current_hash,
            'capacity': self.capacity
        }


    def __repr__(self):
        return f"Block(Index: {self.index}, Hash: {self.current_hash}, Prev Hash: {self.previous_hash}, Transactions: {len(self.transactions)})"

