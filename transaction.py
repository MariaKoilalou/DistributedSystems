import hashlib
import json
import Crypto
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

class Transaction:
    def __init__(self, sender_address, receiver_address, type_of_transaction, amount, message=None, nonce=0):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.type_of_transaction = type_of_transaction
        self.amount = amount
        self.message = message
        self.nonce = nonce
        self.transaction_id = self.calculate_transaction_id()
        self.signature = None  # To be set by the transaction signing method


    def calculate_transaction_id(self):
        """
        Generate a transaction ID by hashing some of the transaction's details.
        """
        transaction_details = json.dumps({
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'amount': self.amount,
            'message': self.message,
            'nonce': self.nonce
        })
        return hashlib.sha256(transaction_details.encode()).hexdigest()

    def to_dict(self):
        """
        Convert the transaction details into a dictionary for easier processing and transmission.
        """
        return {
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'type_of_transaction': self.type_of_transaction,
            'amount': self.amount,
            'message': self.message,
            'nonce': self.nonce,
            'transaction_id': self.transaction_id,
            'signature': self.signature
        }
    

    def verify_signature(self):
        """
        Verify the signature of the transaction using the provided public key.
        """
        verifier = pkcs1_15.new(RSA.import_key(self.sender_address))
        transaction_data = json.dumps(self.to_dict(), sort_keys=True).encode()
        transaction_hash = SHA256.new(transaction_data)
        return verifier.verify(transaction_hash, self.signature)