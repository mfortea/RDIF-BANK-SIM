# server.py
import asyncio
import websockets
import json  # Importa el módulo json

connected_clients = set()

async def echo(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Decodifica el mensaje JSON
            data = json.loads(message)
            card_data = data.get("card_data", "")

            # Procesa o verifica el campo card_data
            if card_data.startswith("card"):
                response_message = f"Valid card data received: {card_data}"
            else:
                response_message = "Invalid card data"

            # Envía la respuesta a todos los clientes
            for client in connected_clients:
                if client != websocket:
                    await client.send(response_message)
    finally:
        connected_clients.remove(websocket)

start_server = websockets.serve(echo, "localhost", 8077)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
