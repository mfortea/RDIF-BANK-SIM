import base64
import hashlib
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import json

reader = SimpleMFRC522()

def decrypt_data(data):
    """Desencripta los datos almacenados en la tarjeta."""
    return base64.b64decode(data.encode())

def read_card():
    """Lee datos de una tarjeta RFID."""
    try:
        id, data = reader.read()
        return data
    except Exception as e:
        print(f"Error al leer la tarjeta: {e}")
        return None

def load_users():
    """Carga la información de los usuarios desde un archivo JSON."""
    try:
        with open("users.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Archivo de usuarios no encontrado.")
        return {}

def verify_user(hash_sequence, user_id):
    """Verifica si la secuencia de hash corresponde al usuario."""
    users = load_users()
    if user_id not in users:
        print("Usuario no encontrado.")
        return False

    stored_hashes = users[user_id]["hash_sequence"]
    for stored_hash, input_hash in zip(stored_hashes, hash_sequence):
        if stored_hash != input_hash:
            return False
    return True

def main():
    user_id = input("Ingrese el ID de usuario: ")
    hash_sequence = []

    for i in range(1, 5):
        print(f"Acercar la Tarjeta {i} al lector...")
        card_data = read_card()
        if card_data:
            decrypted_data = decrypt_data(card_data)
            hash_sequence.append(decrypted_data)

    if verify_user(hash_sequence, user_id):
        print("Usuario autenticado con éxito.")
    else:
        print("Falló la autenticación del usuario.")

    GPIO.cleanup()

if __name__ == "__main__":
    main()
