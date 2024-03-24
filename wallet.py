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
        # Construct the transaction details
        transaction_details = {
            'sender_address': self.address,  # Use the wallet's address as the sender
            'recipient_address': recipient_address,
            'amount': amount,
            'message': message,
            'nonce': nonce,
        }

        transaction_details['signature'] = self.sign_transaction(transaction_details)
        return transaction_details
    
    # Add methods to update and get the wallet's balance as needed
    def update_balance(self, amount):
        """
        Update the wallet's balance.
        """
        self.balance += amount

    def get_balance(self):
        """
        Get the current balance of the wallet.
        """
        return self.balance

    def show_balance(self):
        """
        Print the current balance of the wallet to the console.
        """
        print(f"Current Balance: {self.balance} BTC")


# Example usage
if __name__ == "__main__":
    my_wallet = Wallet()
    transaction = {"from": my_wallet.address, "to": "RecipientPublicKey", "amount": 100}
    signature = my_wallet.sign_transaction(transaction)

    # Simulate sending the transaction and signature to a recipient
    print("Transaction:", transaction)
    print("Signature:", signature)

    # The recipient (or a node in the network) would verify the signature like this
    is_valid = my_wallet.verify_signature(transaction, signature, my_wallet.public_key)
    print("Is the signature valid?", is_valid)