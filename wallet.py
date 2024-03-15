import Crypto
from Crypto.PublicKey import RSA
import base64

class Wallet:
    def __init__(self):
        key_length = 1024
        rsaKeys = RSA.generate(key_length)
        self.private_key = rsaKeys.export_key().decode('utf-8')  # Convert bytes to string
        self.public_key = base64.b64encode(rsaKeys.publickey().export_key()).decode('utf-8')  # Convert bytes to Base64 string
        self.address = self.public_key  # You may want to store the address in a different format
        self.utxos = []
        self.utxoslocal = []
        self.balance = 0

    # Your other wallet methods here


# import Crypto
# import Crypto.Random
# from Crypto.Hash import SHA
# from Crypto.PublicKey import RSA
# from Crypto.Signature import PKCS1_v1_5

# import hashlib
# import json
# from time import time
# from urllib.parse import urlparse
# from uuid import uuid4

# class Wallet:

# 	def __init__(self):
# 		key_length = 1024
# 		rsaKeys = RSA.generate(key_length)
# 		self.private_key = rsaKeys.export_key()
# 		self.public_key = rsaKeys.publickey().export_key()
# 		self.address = self.public_key
# 		self.utxos = []
# 		self.utxoslocal = []
# 		self.balance = 0

# 	# def get_balance(self):
#     #     """
#     #     Get the current balance of the wallet.
#     #     """
#     #     return self.balance
	
# 	# def update_balance(self, amount):
#     #     """
#     #     Update the balance of the wallet by adding the given amount.
#     #     """
#     #     self.balance += amount

#     # def deduct_balance(self, amount):
#     #     """
#     #     Deduct the given amount from the wallet balance.
#     #     """
#     #     if self.balance >= amount:
#     #         self.balance -= amount
#     #         return True
#     #     else:
#     #         return False