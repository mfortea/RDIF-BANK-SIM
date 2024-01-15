# CARD_CREATOR.PY

import os
import dotenv
import mariadb
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import random
import hashlib

# Cargar variables de entorno desde el archivo .env
dotenv.load_dotenv()
simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"

# Solo importar bibliotecas RFID si no estamos en modo de simulación
if not simulation_mode:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO

# Conectar a la base de datos
conn = mariadb.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor()

# Generar clave AES y nonce
aes_key = os.urandom(32) 
nonce = random.randbytes(16) 

def encrypt_aes(data, key, nonce):
    if isinstance(data, str):
        data = data.encode()
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


# Función para generar un nonce aleatorio
def generate_nonce():
    return random.randbytes(16)

def write_data(data, index, simulation):
    if simulation:
        with open(f"card_{index}.txt", "w") as file:
            if isinstance(data, bytes):
                file.write(data.hex())  # Si es bytes, convertir a hexadecimal
            else:
                file.write(data)  # Si ya es una cadena, escribir directamente
    else:
        # Escribir datos en una tarjeta real
        reader = SimpleMFRC522()
        try:
            reader.write(data)
        finally:
            # Limpiar los pines GPIO
            GPIO.cleanup()

def main():
    enable_encryption = os.getenv("ENABLE_ENCRYPTION", "True").lower() == "true"
    simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"

    # Obtener nombre de usuario y contraseña
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Validar y limitar el tamaño de la contraseña
    if len(password) > 16:
        print("Password is too long. Maximum 16 characters.")
        return

    if enable_encryption:
        encrypted_password = encrypt_aes(password, aes_key, nonce)
    else:
        encrypted_password = password.encode()  # Asegúrate de que sea bytes


    # Guardar usuario en la base de datos con el nonce
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("INSERT INTO users (username, password, nonce) VALUES (?, ?, ?)", 
                   (username, password_hash, nonce.hex()))

    conn.commit()

    # Dividir la información y escribir en las tarjetas
    data_parts = [aes_key.hex(), nonce.hex(), encrypted_password.hex()]  # Convertir a hexadecimal
    max_chunk_size = 48  # Tamaño máximo de las tarjetas RFID
    card_data = []

    for part in data_parts:
        while len(part) > 0:
            chunk = part[:max_chunk_size]
            part = part[max_chunk_size:]
            card_data.append(chunk)

    # Escribir en las tarjetas RFID o en archivos de simulación
    for i, chunk in enumerate(card_data):
        write_data(chunk, i, simulation_mode)

    # Cerrar la conexión a la base de datos
    conn.close()


def cleanup_GPIO():
    if not simulation_mode:
        GPIO.cleanup()


# Llamar a la función principal
if __name__ == "__main__":
    try:
        main()
    finally:
        if not simulation_mode:
            cleanup_GPIO()