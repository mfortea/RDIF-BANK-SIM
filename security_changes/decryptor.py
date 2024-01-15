# Importar bibliotecas necesarias
import os
import dotenv
import mariadb
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.hashes import SHA256
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

# Configurar el esquema de encriptación
padding.OAEP(
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

# Función para desencriptar la contraseña
def decrypt_password(encrypted_password, private_key, hash_algorithm):
    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hash_algorithm),
            algorithm=hash_algorithm,
            label=None
        )
    )
    return decrypted_password.decode()

# Obtener el nonce de la base de datos para un usuario específico
def get_nonce_for_user(username):
    cursor.execute("SELECT nonce FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

# Función para verificar y desencriptar los datos de la tarjeta
def verify_and_decrypt_card_data(data, stored_nonce, private_key, hash_algorithm):
    try:
        # Desencriptar la información de la tarjeta
        decrypted_data = decrypt_password(data, private_key, hash_algorithm)

        # Verificar el nonce
        if decrypted_data[-16:] == stored_nonce:
            return decrypted_data[:-16]  # Devolver la contraseña sin el nonce
        else:
            return None  # El nonce no coincide, la información es incorrecta
    except Exception as e:
        print("Error al desencriptar la tarjeta:", str(e))
        return None

# Función principal
def main():
    # Obtener nombre de usuario
    username = input("Ingrese el nombre de usuario: ")

    # Obtener la clave privada del usuario
    with open(f"private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    # Leer el nonce del usuario
    stored_nonce = get_nonce_for_user(username)

    if stored_nonce is not None:
        try:
            decrypted_passwords = []
            for i in range(4):
                print(f"Acerque la tarjeta {i + 1} al lector para verificar los datos.")
                data = reader.read()
                card_data = data[1]
                decrypted_data = verify_and_decrypt_card_data(card_data, stored_nonce, private_key, SHA256())
                if decrypted_data is not None:
                    decrypted_passwords.append(decrypted_data)

            if len(decrypted_passwords) > 0:
                print("Contraseñas válidas:")
                for password in decrypted_passwords:
                    print(password)
            else:
                print("Ninguna tarjeta válida.")
        except Exception as e:
            print("Error al leer las tarjetas:", str(e))
    else:
        print("Usuario no encontrado en la base de datos.")

    conn.close()

# Llamar a la función principal
if __name__ == "__main__":
    main()
