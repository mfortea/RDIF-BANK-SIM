# DECRYPTOR.PY
import os
import dotenv
import mariadb
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import time

# Cargar variables de entorno
dotenv.load_dotenv()
simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"
enable_encryption = os.getenv("ENABLE_ENCRYPTION", "True").lower() == "true"

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

def decrypt_aes(encrypted_data, key, nonce):
    if not simulation_mode:
    # Asegurarse de que todos los parámetros sean bytes para el modo real
        if isinstance(encrypted_data, str):
            encrypted_data = bytes.fromhex(encrypted_data)
        if isinstance(key, str):
            key = bytes.fromhex(key)
        if isinstance(nonce, str):
            nonce = bytes.fromhex(nonce)
    
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()


def read_data(index, simulation):
    if simulation:
        with open(f"card_{index}.txt", "r") as file:
            return bytes.fromhex(file.read())
    else:
        reader = SimpleMFRC522()
        try:
            print(f"Approach card {index + 1} to the RFID reader...")
            data = reader.read()
            card_data = data[1]
            print(f"Data from card {index + 1} read >>> Remove the card from the reader")
            time.sleep(2)
            return card_data.strip()
        finally:
            GPIO.cleanup()


def main():
    while True:
        username = input("Enter username: ")
        cursor.execute("SELECT password, nonce FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()

        if not user_data:
            print("Username doesn't exist.")
            continue

        stored_encrypted_password_hex, stored_nonce_hex = user_data
        stored_nonce = bytes.fromhex(stored_nonce_hex)

        if not simulation_mode:
            aes_key_part1 = bytes.fromhex(read_data(0, simulation_mode))
            aes_key_part2 = bytes.fromhex(read_data(1, simulation_mode))
            card_nonce = bytes.fromhex(read_data(2, simulation_mode))
        else:
            aes_key_part1 = (read_data(0, simulation_mode))
            aes_key_part2 = (read_data(1, simulation_mode))
            card_nonce = (read_data(2, simulation_mode))

        card_encrypted_password_hex = read_data(3, simulation_mode)
         # Verificar que el nonce de la tarjeta coincide con el almacenado
        print("Nonce from the card: ", card_nonce)
        print("Nonce from the database: ", stored_nonce)
        if card_nonce != stored_nonce:
            print("Nonce mismatch. Access Denied.")
            continue

        aes_key = aes_key_part1 + aes_key_part2

        if not simulation_mode:
            card_encrypted_password = bytes.fromhex(card_encrypted_password_hex)
        else:
            card_encrypted_password = (card_encrypted_password_hex)

        # Desencriptar contraseña
        decrypted_password_bytes = decrypt_aes(card_encrypted_password, aes_key, card_nonce)
        
        # Comparar hashes de contraseñas
        decrypted_password_hash = hashlib.sha256(decrypted_password_bytes).hexdigest()
        is_valid = decrypted_password_hash == stored_encrypted_password_hex

        # Acceso al sistema
        print("Access Granted!" if is_valid else "Access Denied")
        break


    # Cerrar la conexión a la base de datos
    conn.close()

if __name__ == "__main__":
    main()

