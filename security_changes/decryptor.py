import os
import dotenv
import mariadb
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.hashes import SHA256
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

# Cargar clave privada
with open("private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
        backend=default_backend()
    )

# Función para desencriptar la contraseña
def decrypt_password(encrypted_password):
    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=SHA256()),
            algorithm=SHA256(),
            label=None
        )
    )
    return decrypted_password.decode()

# Función para verificar la información de la tarjeta y comparar contraseñas
def verify_and_decrypt_card_data(data, stored_nonce):
    try:
        # Desencriptar la información de la tarjeta
        decrypted_data = decrypt_password(data)

        # Verificar el nonce
        if decrypted_data[-16:] == stored_nonce:
            return decrypted_data[:-16]  # Devolver la contraseña sin el nonce
        else:
            return None  # El nonce no coincide, la información es incorrecta
    except Exception as e:
        print("Error al desencriptar la tarjeta:", str(e))
        return None

# Leer el nonce de la base de datos para verificar
cursor.execute("SELECT nonce FROM nonce_table WHERE id = 1")
stored_nonce = cursor.fetchone()[0]

# Leer información de las tarjetas
reader = SimpleMFRC522()

for i in range(4):
    try:
        print(f"Acerque la tarjeta {i+1} al lector para verificar los datos.")
        card_data = reader.read()
        decrypted_password = verify_and_decrypt_card_data(card_data, stored_nonce)

        if decrypted_password is not None:
            # Buscar la contraseña en la base de datos y comparar
            cursor.execute("SELECT password FROM users WHERE password = ?", (decrypted_password,))
            match = cursor.fetchone()
            if match:
                print(f"Tarjeta {i+1}: Contraseña válida.")
            else:
                print(f"Tarjeta {i+1}: Contraseña no válida.")
        else:
            print(f"Tarjeta {i+1}: Información no válida.")
    except Exception as e:
        print("Error al leer la tarjeta:", str(e))

conn.close()
