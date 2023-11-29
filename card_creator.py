import base64
import bcrypt
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

def encrypt_data(data):
    """ Encriptar los datos para almacenar en la tarjeta. """
    return base64.b64encode(data.encode()).decode()

def write_card(reader, data):
    """ Escribir datos en la tarjeta RFID. """
    try:
        print("Please place the card to be written on the reader...")
        reader.write(data)
        print("Data written successfully.")
    except Exception as e:
        print(f"Error writing to card: {e}")

def create_user_card(reader):
    """ Crear una tarjeta de usuario. """
    username = input("Enter the username to encode: ")
    encrypted_username = encrypt_data(username)
    write_card(reader, encrypted_username)

def create_auth_card(reader):
    """ Crear una tarjeta de autenticación. """
    auth_data = "SharedAuthData"  # Este es el dato común en todas las tarjetas de autenticación
    encrypted_auth_data = encrypt_data(auth_data)
    write_card(reader, encrypted_auth_data)

def main():
    reader = SimpleMFRC522()

    try:
        while True:
            print("\nCard Creator")
            print("1. Create User Card")
            print("2. Create Auth Card")
            choice = input("Enter your choice (1-2): ")

            if choice == '1':
                create_user_card(reader)
            elif choice == '2':
                create_auth_card(reader)
            else:
                print("Invalid choice. Please enter 1 or 2.")

            if input("\nDo you want to create another card? (yes/no): ").lower() != 'yes':
                break
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
