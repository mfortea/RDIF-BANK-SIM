import json
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

reader = SimpleMFRC522()

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

def verify_user(user_id, card_data):
    """Verifica si las claves reconstruidas coinciden con las almacenadas."""
    users = load_users()
    if user_id not in users:
        print("Usuario no encontrado.")
        return False

    stored_keys = users[user_id]['key1'] + users[user_id]['key2']
    reconstructed_keys = b''.join(card_data)

    return stored_keys == reconstructed_keys

def main():
    user_id = input("Ingrese el ID de usuario: ")
    card_data = []

    for i in range(4):
        print(f"Acercar la Tarjeta {i+1} al lector...")
        data = read_card()
        if data:
            card_data.append(data)

    if verify_user(user_id, card_data):
        print("Usuario autenticado con éxito.")
    else:
        print("Falló la autenticación del usuario.")

    GPIO.cleanup()

if __name__ == "__main__":
    main()
