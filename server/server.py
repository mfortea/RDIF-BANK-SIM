import asyncio
import websockets
import json
import os
import subprocess
import ssl
import signal
from dotenv import load_dotenv
import base64

def clear_terminal():
    if os.name == 'nt':
        subprocess.run('cls', shell=True)
    else:
        subprocess.run('clear', shell=True)

def load_users():
    with open("users.json", "r") as file:
        return json.load(file)

def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

users_file_lock = asyncio.Lock()

async def manage_users(websocket, is_boss):
    if not is_boss:
        return

    while True:
        command = await websocket.recv()
        async with users_file_lock:
            users = load_users()
            if command == "list_users":
                user_list = []
                for user in users:
                    decoded_username = base64.b64decode(user['username']).decode()
                    user_info = f"Username: {decoded_username} - {'Is Boss' if user['boss'] else 'Not Boss'} - {'User enabled' if user['enabled'] else 'User disabled'}"
                    user_list.append(user_info)
                await websocket.send(json.dumps(user_list))

            elif command.startswith("modify_user"):
                _, username, status = command.split()
                encoded_username = base64.b64encode(username.encode()).decode()
                decoded_username = base64.b64decode(encoded_username).decode()
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
                        return False, "User disabled", user_card, False
                    return True, "USER_OK", base64.b64decode(user_card).decode(), user["boss"]
            return False, "User not authorized", user_card, False
    except Exception as e:
        print(f"Error during user card verification: {e}")
        return False, "User card verification error", user_card, False


auth_card_content_encrypted = base64.b64encode("SharedAuthData".encode()).decode()  # Reemplazar con tu valor real

async def authenticate_user(auth_card, auth_card_content):
    try:
        auth_card_decoded = base64.b64decode(auth_card).decode()
        auth_card_decoded = auth_card_decoded.strip() 
        auth_card_content = auth_card_content.strip()
        print("DEL SERVIDOR: LA TARJETA TIENE: " + auth_card_decoded)
        print("DEL SERVIDOR: SE ESTÁ COMPARANDO CON: " + auth_card_content)
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
    username = "UNKNOWN USER"
    connection_active = True  # Flag para controlar la vida de la conexión

    try:
        while connection_active:
            try:
                # Espera por mensajes del cliente pero con un timeout
                task = asyncio.wait_for(websocket.recv(), timeout=1.0)
                user_card_data = await task
                user_card = json.loads(user_card_data)["user_card"]
                if user_card is None:
                    print("ERROR: BAD USER DATA RECEIVED")
                    return
                user_valid, message, username, is_boss = await verify_user_card(user_card)
                if not user_valid:
                    await websocket.send(message)
                    continue 

                boss_status = 'boss' if is_boss else 'not_boss'
                await websocket.send(f"USER_OK;{boss_status}")

                auth_card_data = await websocket.recv()
                auth_card = json.loads(auth_card_data)["auth_card"]

                auth_valid, message = await authenticate_user(auth_card, "SharedAuthData")

                if not auth_valid:
                    await websocket.send(message)
                    continue

                await websocket.send("AUTH_OK")
                print(f"\n-> USER {username} CONNECTED")

                if is_boss:
                    await manage_users(websocket, is_boss)

            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                connection_active = False
            except KeyError:
                print("ERROR: BAD AUTH DATA RECEIVED")

    except websockets.exceptions.ConnectionClosedOK:
        print(f"-> USER {username} DISCONNECTED")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"-> USER {username} DISCONNECTED with error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        print(f"-> USER {username} DISCONNECTED")


# Función para manejar el cierre del servidor
async def shutdown(server, loop):
    print("\n\nSERVER CLOSED")
    server.close()
    await server.wait_closed()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    loop.stop()

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

    def signal_handler():
        asyncio.ensure_future(shutdown(server, loop))

    loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        start_server = websockets.serve(
            payment_processor, 
            SERVER_MODE, 
            PORT,
            ssl=ssl_context,
            ping_interval=300,
            ping_timeout=300,
            close_timeout=300
        )
        clear_terminal()
        print("* SERVER RUNNING...")
        server = loop.run_until_complete(start_server)

        loop.run_forever()
    except OSError as e:
        if e.errno == 48:  # Número de error para 'address already in use'
            print("PORT ALREADY IN USE")
        else:
            print(f"OSError: {e}")
    finally:
        loop.close()    