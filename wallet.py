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
        self.utxos = []  # List to store unspent transaction outputs

    def update_utxos(self, new_utxos):
        """
        Update the wallet's UTXOs after receiving new transactions.
        """
        self.utxos.extend(new_utxos)

    def select_utxos(self, amount):
        """
        Select UTXOs to cover the desired amount.
        """
        selected_utxos = []
        total_amount = 0

        for utxo in self.utxos:
            total_amount += utxo["amount"]
            selected_utxos.append(utxo)
            if total_amount >= amount:
                break

        return selected_utxos, total_amount

    def sign_transaction(self, transaction):
        """
        Sign a transaction with the wallet's private key.
        """
        if self.address == "0" and private_key == "genesis_signature":
            self.signature = "genesis_signature"
        else:
            transaction_string = json.dumps(transaction, sort_keys=True)
            transaction_bytes = transaction_string.encode('utf-8')
            transaction_hash = SHA256.new(transaction_bytes)
            private_key = RSA.import_key(self.private_key)
            signer = pkcs1_15.new(private_key)
            signature = signer.sign(transaction_hash)
            return base64.b64encode(signature).decode('utf-8')
        # Return the signature in Base64 to ensure it's easily transmittable
        return base64.b64encode(signature).decode('utf-8')

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

    def create_signed_transaction(self, recipient_address, amount, message, nonce):
        """
        Create a new transaction with the given details and sign it with the wallet's private key.
        """
        total_amount = self.select_utxos(amount)
        if total_amount < amount:
            raise Exception("Insufficient funds")
        
        change = total_amount - amount
        outputs = [{"recipient": recipient_address, "amount": amount}]
        if change > 0:
            # Add change output back to the sender's UTXOs
            outputs.append({"recipient": self.address, "amount": change})
        
        # Construct the transaction details
        transaction_details = {
            'sender_address': self.address,  # Use the wallet's address as the sender
            'recipient_address': recipient_address,
            'amount': amount,
            'message': message,
            'nonce': nonce,
            'outputs': outputs
        }

        transaction_details['signature'] = self.sign_transaction(transaction_details)
        return transaction_details
    
