import asyncio
import websockets
import json
import os
import ssl
import signal
from dotenv import load_dotenv

# Función para procesar los pagos
async def payment_processor(websocket, path):
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


# Función para manejar el cierre del servidor
async def shutdown(server, event):
    print("SERVER CLOSED")
    server.close()
    await server.wait_closed()
    event.set()

if __name__ == "__main__":
    load_dotenv()

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
        ssl=ssl_context
    )

    server = loop.run_until_complete(start_server)

    # Función para manejar la señal SIGINT (Ctrl+C)
    def signal_handler():
        asyncio.create_task(shutdown(server, stop_event))

    loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        loop.run_until_complete(stop_event.wait())  # Esperar a que se active el evento de parada
    finally:
        loop.close()
