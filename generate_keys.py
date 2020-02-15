from builtins import print

from Crypto.PublicKey import RSA
from Crypto import Random
import base64
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES,PKCS1_OAEP


def generate_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return  str(private_key) ,  str(public_key)

def format_key(key):
    key = key.replace("\\n", "\n")
    key = key.replace("'", "")
    key = key[1:]
    return key

def encrypt(public_key, data):
    public_key = format_key(public_key)
    rsa_public_key = RSA.importKey(public_key)
    rsa_public_key = PKCS1_OAEP.new(rsa_public_key)
    encrypted_text = rsa_public_key.encrypt(data.encode())
    return  encrypted_text

def decrypt(private_key, data):
    private_key = format_key(private_key)
    rsa_private_key = RSA.importKey(private_key)
    rsa_private_key = PKCS1_OAEP.new(rsa_private_key)
    decrypted_text = rsa_private_key.decrypt(data)

    return decrypted_text

