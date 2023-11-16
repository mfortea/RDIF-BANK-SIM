# client.py
import asyncio
import websockets
import json

async def send_card_data():
    async with websockets.connect("ws://localhost:8077") as websocket:
        # Solicitar datos de la tarjeta RFID desde la consola
        card_data_input = input("Ingrese los datos de la tarjeta RFID: ")
        card_data = {"card_data": card_data_input}

        await websocket.send(json.dumps(card_data))
        response = await websocket.recv()
        print(response)

asyncio.get_event_loop().run_until_complete(send_card_data())
