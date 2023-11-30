import asyncio
import websockets
import json
import os
import ssl
import signal
from dotenv import load_dotenv
import base64

def load_users():
    with open("users.json", "r") as file:
        return json.load(file)

def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

async def manage_users(websocket, is_boss):
    if not is_boss:
        return

    while True:
        command = await websocket.recv()
        users = load_users()

        if command == "list_users":
            user_list = []
            for user in users:
                # Decodificando el nombre de usuario de Base64 para mostrarlo
                decoded_username = base64.b64decode(user['username']).decode()
                user_info = f"Username: {decoded_username} - {'Is Boss' if user['boss'] else 'Not Boss'} - {'User enabled' if user['enabled'] else 'User disabled'}"
                user_list.append(user_info)
            await websocket.send(json.dumps(user_list))
        elif command.startswith("modify_user"):
            _, username, status = command.split()
            # Codificando el nombre de usuario ingresado para la comparación
            encoded_username = base64.b64encode(username.encode()).decode()
            for user in users:
                if user['username'] == encoded_username:
                    user['enabled'] = status == 'enable'
                    save_users(users)
                    await websocket.send(f"User {decoded_username} updated.")
                    break
            else:
                await websocket.send(f"User {username} not found.")
        elif command.startswith("delete_user"):
            _, username = command.split()
            encoded_username = base64.b64encode(username.encode()).decode()
            original_count = len(users)
            users = [user for user in users if user['username'] != encoded_username]
            if len(users) < original_count:
                save_users(users)
                await websocket.send(f"User {username} deleted.")
            else:
                await websocket.send(f"User {username} not found.")
        elif command.startswith("add_user"):
            _, username, boss_str, enabled_str = command.split()
            encoded_username = base64.b64encode(username.encode()).decode()
            is_boss = boss_str == 'yes'
            is_enabled = enabled_str == 'yes'
            # Verifica si el usuario ya existe
            if any(user["username"] == encoded_username for user in users):
                await websocket.send("Error: The user already exists")
            else:
                users.append({"username": encoded_username, "enabled": is_enabled, "boss": is_boss})
                save_users(users)
                await websocket.send(f"User {username} added.")
        elif command == "exit":
            break

async def verify_user_card(user_card):
    user_card = user_card.strip()  # Eliminar espacios en blanco
    try:
        with open("users.json", "r") as file:
            users = json.load(file)
            for user in users:
                user_name = user["username"].strip()  # Eliminar espacios en blanco
                if user_card == user_name:
                    if not user["enabled"]:
                        return False, "User disabled", None
                    return True, "USER_OK", base64.b64decode(user_card).decode(), user["boss"]
            return False, "User not authorized", None
    except Exception as e:
        print(f"Error during user card verification: {e}")
        return False, "User card verification error", None

auth_card_content_encrypted = base64.b64encode("SharedAuthData".encode()).decode()  # Reemplazar con tu valor real

async def authenticate_user(auth_card, auth_card_content):
    try:
        auth_card_decoded = base64.b64decode(auth_card).decode()
        auth_card_decoded = auth_card_decoded.strip() 
        auth_card_content = auth_card_content.strip()
        if auth_card_decoded != auth_card_content:
            return False, "Invalid Auth Card"
        return True, ""
    except base64.binascii.Error as e:
        print(f"Base64 decoding error: {e}")
        return False, "Auth card decoding error"
    except UnicodeDecodeError as e:
        print(f"Unicode decoding error: {e}")
        return False, "Auth card unicode error"
    except Exception as e:
        print(f"General error during auth card verification: {e}")
        return False, "Auth card verification error"


async def payment_processor(websocket, path):
    user_card_data = await websocket.recv()
    user_card = json.loads(user_card_data)["user_card"]

    user_valid, message, username, is_boss = await verify_user_card(user_card)
    if not user_valid:
        await websocket.send(message)
        return
    else:
        boss_status = 'boss' if is_boss else 'not_boss'
        await websocket.send(f"USER_OK;{boss_status}")

    auth_card_data = await websocket.recv()
    auth_card = json.loads(auth_card_data)["auth_card"]

    # Asegúrate de definir o tener accesible auth_card_content
    auth_card_content = "SharedAuthData"  # Reemplaza esto con el valor real esperado

    auth_valid, message = await authenticate_user(auth_card, auth_card_content)

    if not auth_valid:
        await websocket.send(message)
        return
    else:
        await websocket.send("AUTH_OK")

    if is_boss:
        await manage_users(websocket, is_boss)

    print(f"\n-> {username} CONNECTED")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Handling user choices here (implementation pending)
            pass
    finally:
        connected_clients.remove(websocket)
        print(f"-> {username} DISCONNECTED")


# Función para manejar el cierre del servidor
async def shutdown(server, event):
    print("\n\nSERVER CLOSED")
    server.close()
    await server.wait_closed()
    event.set()

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    grandparent_directory = os.path.dirname(parent_directory)
    env_file_path = os.path.join(grandparent_directory, '.env')
    load_dotenv(env_file_path)

    PORT = os.getenv("WEBSOCKET_PORT")
    SERVER_MODE = os.getenv("SERVER_MODE")
    CERT = os.getenv("CERT_PATH")
    KEY = os.getenv("KEY_PATH")

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(CERT, KEY)

    connected_clients = set()

    loop = asyncio.get_event_loop()

    stop_event = asyncio.Event()

    start_server = websockets.serve(
        payment_processor, 
        SERVER_MODE, 
        PORT,
        ssl=ssl_context,
        ping_interval=300,
        ping_timeout=300,
        close_timeout=300
    )
    print("* SERVER RUNNING...")
    server = loop.run_until_complete(start_server)

    def signal_handler():
        asyncio.create_task(shutdown(server, stop_event))

    loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        loop.run_until_complete(stop_event.wait())
    finally:
        loop.close()
