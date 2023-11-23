import asyncio
import websockets
import json
from dotenv import load_dotenv
import os

# Loading variables from .env
load_dotenv()

PORT = os.getenv("WEBSOCKET_PORT")
SERVER_MODE = os.getenv("SERVER_MODE")

connected_clients = set()

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

start_server = websockets.serve(payment_processor, SERVER_MODE, PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
