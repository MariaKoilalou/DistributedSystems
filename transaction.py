import base64
import hashlib
import json
import Crypto
import jsonpickle
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

class Transaction:
    def __init__(self, sender_address, receiver_address, type_of_transaction, amount, message=None, nonce=0, signature = None):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.type_of_transaction = type_of_transaction
        self.amount = amount
        self.message = message
        self.nonce = nonce
        # self.transaction_id = self.calculate_transaction_id()
        self.transaction_id = self.hash() 


    def hash(self):

        transaction_details = json.dumps({
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'amount': self.amount,
            'message': self.message,
            'nonce': self.nonce
        })
                    
        tr_inputs = str(jsonpickle.encode(transaction_details))
        block_to_byte = bytes(str(self.sender_address) + str(self.receiver_address) + str(self.amount) + tr_inputs, 'utf-8')
        return SHA256.new(block_to_byte)

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
        return hashlib.sha256(transaction_details.encode('utf-8'))

    def to_dict(self):
        
        return {
            'sender_address': base64.b64encode(self.sender_address).decode() if isinstance(self.sender_address, bytes) else self.sender_address,
            'receiver_address': base64.b64encode(self.receiver_address).decode() if isinstance(self.receiver_address, bytes) else self.receiver_address,
            'type_of_transaction': self.type_of_transaction,
            'amount' : self.amount,
            'message': self.message,
            'nonce': self.nonce,
            'transaction_id' : self.transaction_id.hexdigest(),
            'signature': base64.b64encode(self.signature).decode() if self.signature and isinstance(self.signature, bytes) else self.signature,
        }
        
    def sign_transaction(self, sender_private_key):
        """
        Sign transaction with private key
        """
        signer = pkcs1_15.new(RSA.import_key(sender_private_key))
        self.signature = signer.sign(self.transaction_id)
        return self.signature
    
    def verify_signature(self):
            pk = RSA.import_key(base64.b64decode(self.sender_address))
            verifier = PKCS1_v1_5.new(pk)
            return verifier.verify(self.transaction_id, self.signature)