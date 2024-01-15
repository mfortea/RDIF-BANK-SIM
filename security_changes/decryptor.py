# DECRYPTOR.PY
import os
import dotenv
import mariadb
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib

# Cargar variables de entorno
dotenv.load_dotenv()
simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"
enable_encryption = os.getenv("ENABLE_ENCRYPTION", "True").lower() == "true"

# Conectar a la base de datos
conn = mariadb.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor()

def decrypt_aes(encrypted_data, key, nonce):
    if isinstance(encrypted_data, str):
        encrypted_data = bytes.fromhex(encrypted_data)  # Convertir de hex a bytes si es necesario
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()


def read_data(index, simulation):
    if simulation:
        with open(f"card_{index}.txt", "r") as file:
            return bytes.fromhex(file.read())
    else:
        # Implementación para leer de tarjetas RFID
        pass



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

        card_nonce = read_data(2, simulation_mode)  # Índice 0 para nonce


        if card_nonce != stored_nonce:
            continue

        card_encrypted_password_hex = read_data(3, simulation_mode)  # Índice 3 para la contraseña encriptada
        if isinstance(card_encrypted_password_hex, str):
            card_encrypted_password = bytes.fromhex(card_encrypted_password_hex)
        else:
            card_encrypted_password = card_encrypted_password_hex

        aes_key_part1 = read_data(0, simulation_mode)
        aes_key_part2 = read_data(1, simulation_mode)
        aes_key = aes_key_part1 + aes_key_part2

        # Desencriptar contraseña
        decrypted_password_bytes = decrypt_aes(card_encrypted_password, aes_key, stored_nonce)
        
        # Comparar hashes de contraseñas
        decrypted_password_hash = hashlib.sha256(decrypted_password_bytes).hexdigest()
        is_valid = decrypted_password_hash == stored_encrypted_password_hex

        # Acceso al sistema
        print("Access Granted" if is_valid else "Access Denied")
        break

    # Cerrar la conexión a la base de datos
    conn.close()

if __name__ == "__main__":
    main()

