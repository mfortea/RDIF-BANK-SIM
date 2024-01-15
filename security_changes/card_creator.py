# Importar bibliotecas necesarias
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


# Configurar el esquema de encriptación
oaep_padding = padding.OAEP(
mgf=padding.MGF1(algorithm=SHA256()),
algorithm=SHA256(),
label=None
)


# Cargar variables de entorno desde el archivo .env
dotenv.load_dotenv()

# Conectar a la base de datos
conn = mariadb.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor()

# Función para encriptar la contraseña
def encrypt_password(password, public_key):
    return public_key.encrypt(
    password.encode(),
    oaep_padding
    )

# Función para generar un nonce aleatorio
def generate_nonce():
    return random.randbytes(16)

# ... (código previo)

# Función para escribir en una tarjeta específica
def write_to_card(data, card_number):
    try:
        print(f"Acerque la tarjeta {card_number + 1} al lector para escribir los datos.")
        data_str = str(data)  # Convierte data a una cadena (string)
        reader.write(data_str)
        print(f"Datos escritos en la tarjeta {card_number + 1}.")

        # Agrega una pausa de 2 segundos
        time.sleep(2)
    finally:
        GPIO.cleanup()


# Función principal
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

    # Validar y limitar el tamaño de la contraseña
    if len(password) > 40:  # Ejemplo de límite de tamaño
        print("La contraseña es demasiado larga. Máximo 40 caracteres.")
        return

    # Encriptar contraseña
    encrypted_password = encrypt_password(password, public_key)

    # Generar nonce
    nonce = generate_nonce()

    # Guardar usuario en la base de datos con el nonce
    cursor.execute("INSERT INTO users (username, password, nonce) VALUES (?, ?, ?)", (username, encrypted_password, nonce))
    conn.commit()

    # Dividir la información y escribir en las tarjetas
    data_parts = [nonce, public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo), encrypted_password]

    # Limitar el tamaño de cada parte
    max_chunk_size = 48  # Tamaño máximo de las tarjetas RFID
    card_data = [[] for _ in range(len(data_parts))]

    for i, part in enumerate(data_parts):
        while len(part) > 0:
            chunk = part[:max_chunk_size]
            part = part[max_chunk_size:]
            card_data[i].append(chunk)

    # Escribir en las tarjetas RFID
    for i, card_chunks in enumerate(card_data):
        for chunk in card_chunks:
            write_to_card(chunk, i)  # Escribir el fragmento en la tarjeta

    # Cerrar la conexión a la base de datos
    conn.close()

def cleanup_GPIO():
    GPIO.cleanup()  


# Llamar a la función principal
if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup_GPIO()
