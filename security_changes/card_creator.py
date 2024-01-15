import os
import dotenv
import mariadb
import hashlib
import random
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric import padding
from mfrc522 import SimpleMFRC522
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

padding.OAEP(
    mgf=padding.MGF1(algorithm=SHA256()),
    algorithm=SHA256(),
    label=None
)

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
def encrypt_password(password, public_key, hash_algorithm):
    return public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hash_algorithm),
            algorithm=hash_algorithm,
            label=None
        )
    )


def write_to_card(data):
    try:
        print("Acerque la tarjeta al lector para escribir los datos.")
        data_str = str(data)  # Convierte data a una cadena (string)
        reader.write(data_str)
        print("Datos escritos en la tarjeta.")
        
        # Agrega una pausa de 2 segundos
        time.sleep(2)
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
    encrypted_password = encrypt_password(password, public_key, SHA256())

    # Guardar usuario en la base de datos
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
    conn.commit()

    # Dividir los datos en cuatro partes iguales
    data_length = len(encrypted_password)
    chunk_size = data_length // 4

    # Escribir en las tarjetas RFID
    for i in range(4):
        start_index = i * chunk_size
        end_index = (i + 1) * chunk_size
        chunk = encrypted_password[start_index:end_index]
        write_to_card(chunk)

    conn.close()

# Llamar a la función principal
if __name__ == "__main__":
    main()
