import os
import dotenv
import mariadb
import hashlib
import random
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from mfrc522 import SimpleMFRC522

dotenv.load_dotenv()

# Conectar a la base de datos
conn = mariadb.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor()

# Funciones
def encrypt_password(password, public_key):
    return public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashlib.sha256()),
            algorithm=hashlib.sha256(),
            label=None
        )
    )

def write_to_card(data):
    reader = SimpleMFRC522()
    try:
        print("Acerque la tarjeta al lector para escribir los datos.")
        reader.write(data)
        print("Datos escritos en la tarjeta.")
    finally:
        GPIO.cleanup()

def main():
    # Cargar clave pública
    with open("public_key.pem", "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )

    # Obtener nombre de usuario y contraseña
    username = input("Ingrese el nombre de usuario: ")
    password = input("Ingrese la contraseña: ")

    # Encriptar contraseña
    encrypted_password = encrypt_password(password, public_key)

    # Guardar usuario en la base de datos
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
    conn.commit()

    # Preparar datos para las tarjetas RFID
    nonce = random.randbytes(16)
    data_chunks = [encrypted_password[i:i + 32] + nonce for i in range(0, len(encrypted_password), 32)]

    # Asegurarse de que cada fragmento tenga 48 bytes
    for i in range(len(data_chunks)):
        data_chunks[i] += random.randbytes(48 - len(data_chunks[i]))

    # Escribir en las tarjetas RFID
    for chunk in data_chunks:
        write_to_card(chunk)

    conn.close()
    
    main()
