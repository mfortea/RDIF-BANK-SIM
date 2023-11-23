import json
import bcrypt

def create_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_data = {username: hashed_password.decode()}

    try:
        with open("users.json", "r+") as file:
            users = json.load(file)
            if username in users:
                print("Error: The username already exists")
                return False
            users.update(user_data)
            file.seek(0)
            json.dump(users, file)
    except FileNotFoundError:
        with open("users.json", "w") as file:
            json.dump(user_data, file)

    print("User created")
    return True

if __name__ == "__main__":
    username = input("New username: ")
    password = input("New password: ")
    create_user(username, password)
