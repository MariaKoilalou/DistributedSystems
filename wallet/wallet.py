import crypto
import crypto.Random
from crypto.Hash import SHA
from crypto.PublicKey import RSA
from crypto.Signature import PKCS1_v1_5

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