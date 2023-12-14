import json
import base64
import hashlib
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

# RFID reader setup
reader = SimpleMFRC522()

def generate_hash_sequence(password, count=4):
    """Generates a hash sequence from a password."""
    hash_sequence = []
    current_hash = password.encode()
    for _ in range(count):
        current_hash = hashlib.sha256(current_hash).digest()
        hash_sequence.append(current_hash)
    return hash_sequence

def encrypt_data(data):
    """Encrypts data for storage on the card."""
    return base64.b64encode(data).decode()

def write_card(data):
    """Writes data to the RFID card."""
    try:
        print("Approach the card to the reader to write...")
        reader.write(data)
        print("Data written successfully.")
    except Exception as e:
        print(f"Error writing to card: {e}")

def load_users():
    """Loads user information from a JSON file."""
    try:
        with open("users.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users(users):
    """Saves user information to a JSON file."""
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

def add_user(user_id, password):
    """Adds a new user and writes the hash sequence to RFID cards."""
    users = load_users()
    if user_id in users:
        print("User already exists.")
        return

    hash_sequence = generate_hash_sequence(password)
    for i, hash_value in enumerate(hash_sequence, start=1):
        encrypted_hash = encrypt_data(hash_value)
        print(f"Writing hash to Card {i}")
        input(f"Press Enter after placing Card {i} on the reader...")
        write_card(encrypted_hash)

    users[user_id] = {"hash_sequence": [encrypt_data(h) for h in hash_sequence]}
    save_users(users)

def remove_user(user_id):
    """Removes a user from the JSON file."""
    users = load_users()
    if user_id in users:
        del users[user_id]
        save_users(users)
        print(f"User {user_id} removed.")
    else:
        print("User not found.")

def main():
    while True:
        print("\nRFID Card Manager")
        print("1. Add User and Create Cards")
        print("2. Remove User")
        choice = input("Enter your choice (1-2): ")

        if choice == '1':
            user_id = input("Enter the user ID: ")
            password = input("Enter a secure password: ")
            add_user(user_id, password)
        elif choice == '2':
            user_id = input("Enter the user ID to remove: ")
            remove_user(user_id)
        else:
            print("Invalid option.")

        if input("\nDo you want to perform another operation? (yes/no): ").lower() != 'yes':
            break

    GPIO.cleanup()

if __name__ == "__main__":
    main()
