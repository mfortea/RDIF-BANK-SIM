import asyncio
import websockets
import json
import os
import ssl
import signal
from dotenv import load_dotenv
import base64

async def verify_user_card(user_card):
    print("SOY EL SERVIDOR Y RECIBO: " + user_card)
    try:
        with open("users.json", "r") as file:
            users = json.load(file)
            for user in users:
                print("Comparando con: " + user["username"])  # Para depuración
                if user_card == user["username"]:
                    print("ESTOY EN EL TRUE")
                    if not user["enabled"]:
                        return False, "User disabled", None
                    return True, "USER_OK", base64.b64decode(user_card).decode()
            print("Ningún usuario coincide")  # Mensaje si no hay coincidencias
            return False, "User not authorized", None
    except Exception as e:
        print(f"Error during user card verification: {e}")
        return False, "User card verification error", None

async def authenticate_user(auth_card, auth_card_content):
    try:
        auth_card_decoded = base64.b64decode(auth_card).decode()
        if auth_card_decoded != auth_card_content:
            return False, "Invalid Auth Card"
        return True, ""
    except Exception as e:
        print(f"Error during auth card verification: {e}")
        return False, "Auth card verification error"

async def payment_processor(websocket, path):
    user_card_data = await websocket.recv()
    user_card = json.loads(user_card_data)["user_card"]

    user_valid, message, username = await verify_user_card(user_card)
    await websocket.send(message)
    if not user_valid:
        return
    else:
        await websocket.send("USER_OK")

    auth_card_data = await websocket.recv()
    auth_card = json.loads(auth_card_data)["auth_card"]

    auth_card_content = "SharedAuthCardContent"
    auth_valid, message = await authenticate_user(auth_card, auth_card_content)

    if not auth_valid:
        await websocket.send(message)
        return
    else:
        await websocket.send("AUTH_OK")

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
