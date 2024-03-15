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
        # Convert the transaction into a string and then to bytes
        transaction_string = str(transaction)
        transaction_bytes = transaction_string.encode('utf-8')

        # Create a hash of the transaction
        transaction_hash = SHA256.new(transaction_bytes)

        # Sign the transaction hash with the private key
        private_key = RSA.import_key(self.private_key)
        signature = pkcs1_15.new(private_key).sign(transaction_hash)

        # Return the signature in Base64 to ensure it's easily transmittable
        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, transaction, signature, sender_public_key):
        """
        Verify the signature of a transaction.
        """
        # Convert the transaction into a string and then to bytes
        transaction_string = str(transaction)
        transaction_bytes = transaction_string.encode('utf-8')

        # Create a hash of the transaction
        transaction_hash = SHA256.new(transaction_bytes)

        # Decode the sender's public key and signature from Base64
        sender_public_key = RSA.import_key(base64.b64decode(sender_public_key))
        signature = base64.b64decode(signature)

        try:
            # Attempt to verify the signature
            pkcs1_15.new(sender_public_key).verify(transaction_hash, signature)
            return True  # The signature is valid
        except (ValueError, TypeError):
            return False  # The signature is invalid

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