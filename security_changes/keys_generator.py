# KEYS GENERATOR

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generar la clave privada RSA
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,  # Puedes elegir 1024, 2048, 4096, etc.
    backend=default_backend()
)

# Obtener la clave pública correspondiente
public_key = private_key.public_key()

# Serializar la clave privada en formato PEM
pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()  # o utiliza un algoritmo de encriptación
)

# Serializar la clave pública en formato PEM
pem_public_key = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

with open("private_key.pem", "wb") as f:
    f.write(pem_private_key)

with open("public_key.pem", "wb") as f:
    f.write(pem_public_key)
