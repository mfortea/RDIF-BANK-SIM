# server.py
import asyncio
import websockets
import json
from dotenv import load_dotenv 
import os

# Loading variables from .env
load_dotenv()

# Ahora puedes acceder a las variables usando os.getenv
PORT = os.getenv("WEBSOCKET_PORT")

connected_clients = set()
amount_to_charge = 0

async def payment_processor(websocket, path):
    global amount_to_charge
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)

            # Diferenciar entre datos de tarjeta y cantidad
            if "amount" in data:
                amount_to_charge = data["amount"]
            elif "card_data" in data:
                card_data = data["card_data"]
                if card_data.startswith("card"):
                    response = f"✅ You paid {amount_to_charge} €"
                else:
                    response = "❌ Invalid Card"
                for client in connected_clients:
                    await client.send(response)
    finally:
        connected_clients.remove(websocket)

start_server = websockets.serve(payment_processor, 'localhost', PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
