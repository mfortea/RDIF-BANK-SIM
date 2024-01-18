from cryptography.fernet import Fernet
import base64
import os
import getpass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

def derive_key(password: bytes, salt: bytes):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def main():
    master_key = Fernet.generate_key()
    password = getpass.getpass("Input a password for encrypting the Master Key: ").encode()
    salt = os.urandom(16)
    password_key = derive_key(password, salt)

    f = Fernet(password_key)
    encrypted_key = f.encrypt(master_key)

    with open("master_key_encrypted", "wb") as key_file:
        key_file.write(salt + b' ' + encrypted_key)

    print("Master Key generated and encrypted as 'master_key_encrypted'")

if __name__ == "__main__":
    main()
