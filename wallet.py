import json
import Crypto
from Crypto.PublicKey import RSA
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

class Wallet:
    def __init__(self):
        key_length = 1024  # You might consider using a larger key size for better security, e.g., 2048
        rsaKeys = RSA.generate(key_length)
        self.private_key = rsaKeys.export_key().decode('utf-8')  # Convert bytes to string for easier handling
        self.public_key = base64.b64encode(rsaKeys.publickey().export_key()).decode('utf-8')  # Convert bytes to Base64 string for easier transmission and storage
        self.address = self.public_key  # In a real application, you might use a more user-friendly address format
        self.balance = 0  # Initially, the wallet's balance is 0
    
    def sign_transaction(self, transaction):
        """
        Sign a transaction with the wallet's private key.
        """        
        transaction_string = json.dumps(transaction, sort_keys=True)
        transaction_bytes = transaction_string.encode('utf-8')
        transaction_hash = SHA256.new(transaction_bytes)
        private_key = RSA.import_key(self.private_key)
        signer = pkcs1_15.new(private_key)
        signature = signer.sign(transaction_hash)
        transaction['signature'] = base64.b64encode(signature).decode('utf-8')
        return transaction


    def verify_signature(self, transaction, signature, sender_public_key):
        """
        Verify the signature of a transaction.
        """
        transaction_string = json.dumps(transaction, sort_keys=True)
        transaction_bytes = transaction_string.encode('utf-8')
        transaction_hash = SHA256.new(transaction_bytes)
        sender_public_key = RSA.import_key(base64.b64decode(sender_public_key))
        signature = base64.b64decode(signature)
        try:
            pkcs1_15.new(sender_public_key).verify(transaction_hash, signature)
            return True
        except (ValueError, TypeError):
            return False

    
