import asyncio
import websockets
import json
import os
import ssl
import signal
from dotenv import load_dotenv
import base64
import bcrypt

# Función para autenticar al usuario
async def authenticate_user(user_card, auth_card, auth_card_content):
    try:
        user_card_decoded = base64.b64decode(user_card).decode()
        auth_card_decoded = base64.b64decode(auth_card).decode()

        if auth_card_decoded != auth_card_content:
            return False, "Invalid Auth Card"

        with open("users.json", "r") as file:
            users = json.load(file)
            for user in users:
                if bcrypt.checkpw(user_card_decoded.encode(), user["username"].encode()):
                    if not user["enabled"]:
                        return False, "User not enabled"
                    return True, ""
            return False, "User not authorized"
    except Exception as e:
        print(f"Error during authentication: {e}")
        return False, "Authentication error"

    return False, "Authentication failed"

async def payment_processor(websocket, path):
    credentials = await websocket.recv()
    user_card, auth_card = json.loads(credentials).values()

    auth_card_content = "SharedAuthCardContent"  # Define the content for the shared auth card
    auth_result, message = await authenticate_user(user_card, auth_card, auth_card_content)

    if not auth_result:
        await websocket.send(message)
        return

    await websocket.send("AUTH_OK")
    username = base64.b64decode(user_card).decode()  # Assuming username is the user card content
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
    env_file_path = os.path.join(parent_directory, '.env')
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
