import asyncio
import websockets
import json
import os
import ssl
import signal
from dotenv import load_dotenv
import base64
import bcrypt

async def authenticate_user(encrypted_credentials):
    try:
        credentials = base64.b64decode(encrypted_credentials).decode()
        username, password = credentials.split(":")

        with open("users.json", "r") as file:
            users = json.load(file)
            hashed_password = users.get(username).encode()

            if bcrypt.checkpw(password.encode(), hashed_password):
                return username
    except Exception as e:
        print(f"Error during authentication: {e}")
    
    return False

async def payment_processor(websocket, path):
    # Autenticación del usuario
    credentials = await websocket.recv()
    username = await authenticate_user(credentials)  # Guarda el nombre de usuario
    if not username:  # Verifica si username es False
        await websocket.send("AUTH_FAILED")
        return

    await websocket.send("AUTH_OK")
    
    print(f"\n-> {username} CONNECTED")  # Muestra el nombre del usuario conectado
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            amount_to_charge = data.get("amount", 0)
            card_data = data.get("card_data", "")

            if card_data.startswith("card"):
                response = f"✅ You paid {amount_to_charge} €"
            else:
                response = "❌ Invalid Card"

            for client in connected_clients:
                await client.send(response)
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

    # Crear contexto SSL
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(CERT, KEY)

    connected_clients = set()

    loop = asyncio.get_event_loop()

    # Evento para señalizar el cierre del servidor
    stop_event = asyncio.Event()

    # Iniciar el servidor

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

    # Función para manejar la señal SIGINT (Ctrl+C)
    def signal_handler():
        asyncio.create_task(shutdown(server, stop_event))

    loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        loop.run_until_complete(stop_event.wait())  # Esperar a que se active el evento de parada
    finally:
        loop.close()
