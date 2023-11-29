import json
import bcrypt

def create_user(username, is_boss, is_enabled):
    # Encriptar el nombre de usuario
    hashed_username = bcrypt.hashpw(username.encode(), bcrypt.gensalt()).decode()

    user_data = {
        "username": hashed_username,
        "boss": is_boss,
        "enabled": is_enabled
    }

    try:
        with open("users.json", "r+") as file:
            users = json.load(file)
            # Verificar si el usuario ya existe (basado en el nombre encriptado)
            if any(user["username"] == hashed_username for user in users):
                print("Error: The user already exists")
                return False
            users.append(user_data)
            file.seek(0)
            json.dump(users, file, indent=4)
    except FileNotFoundError:
        with open("users.json", "w") as file:
            json.dump([user_data], file, indent=4)

    print("User created successfully")
    return True

if __name__ == "__main__":
    username = input("Enter new username: ")
    is_boss = input("Is the user a boss? (yes/no): ").lower() == 'yes'
    is_enabled = input("Is the user enabled? (yes/no): ").lower() == 'yes'
    create_user(username, is_boss, is_enabled)
