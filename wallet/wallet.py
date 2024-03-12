import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

class Wallet:

	def __init__(self):
		key_length = 1024
		rsaKeys = RSA.generate(key_length)
		self.private_key = rsaKeys.export_key()
		self.public_key = rsaKeys.publickey().export_key()
		self.address = self.public_key
		self.utxos = []
		self.utxoslocal = []