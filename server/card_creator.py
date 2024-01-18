# CARD_CREATOR.PY

import os
import dotenv
import mariadb
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import random
import hashlib
import time
from cryptography.fernet import Fernet
import base64
import getpass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


# Cargar variables de entorno desde el archivo .env
dotenv.load_dotenv()
simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"

master_key = None

def decrypt_key(encrypted_key, password):
    f = Fernet(password)
    return f.decrypt(encrypted_key)

def derive_fernet_key(password: bytes, salt: bytes):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def derive_diversified_key(master_key, user_id):
    combined = master_key + user_id.encode()
    return hashlib.sha256(combined).digest()

def read_master_key():
    with open("master_key_encrypted", "rb") as key_file:
        salt, encrypted_key = key_file.read().split(b' ')
    password = getpass.getpass("Input password for Master Key: ").encode()
    password_key = derive_fernet_key(password, salt)
    
    f = Fernet(password_key)
    return f.decrypt(encrypted_key)

# Solo importar bibliotecas RFID si no estamos en modo de simulación
if not simulation_mode:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)

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
                file.write(data.hex())
            else:
                file.write(data)
    else:
        reader = SimpleMFRC522()
        try:
            print(f"Approach card number {index + 1} to the RFID reader...")
            reader.write(data)
            print(f"Data writed to card number {index + 1}.")
            time.sleep(2)
        finally:
            GPIO.cleanup()

def main():
    enable_encryption = os.getenv("ENABLE_ENCRYPTION", "True").lower() == "true"
    simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"

    # Leer la clave maestra existente
    master_key = read_master_key()

    # Obtener nombre de usuario y contraseña
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Validar y limitar el tamaño de la contraseña
    if len(password) > 16:
        print("Password is too long. Maximum 16 characters.")
        return

    nonce = random.randbytes(16)  # Generar un nonce

    if enable_encryption:
        diversified_key = derive_diversified_key(master_key, username)
        encrypted_password = encrypt_aes(password, diversified_key, nonce)
    else:
        encrypted_password = password.encode()

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Guardar usuario en la base de datos con el nonce y la clave diversificada
    cursor.execute("INSERT INTO users (username, password, nonce, diversified_key) VALUES (?, ?, ?, ?)", 
                   (username, password_hash, nonce.hex(), diversified_key.hex()))
    conn.commit()

    # Dividir la información y escribir en las tarjetas
    data_parts = [diversified_key.hex(), nonce.hex(), encrypted_password.hex()]  # Convertir a hexadecimal
    max_chunk_size = 48  # Tamaño máximo de las tarjetas RFID
    card_data = []

    for part in data_parts:
        while len(part) > 0:
            chunk = part[:max_chunk_size]
            part = part[max_chunk_size:]
            card_data.append(chunk)

    # Rellenar card_data para asegurarse de que siempre hay 4 elementos
    while len(card_data) < 4:
        card_data.append("")

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
