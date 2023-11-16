# client.py
import asyncio
import websockets
import json

async def simulate_rfid_card():
    try:
        async with websockets.connect("ws://localhost:8077") as websocket:
            while True:
                # Simular la lectura de una tarjeta RFID
                card_data_input = input("Simular acercar tarjeta RFID (escribe 'cardxxx' o cualquier otra cosa para una tarjeta no válida): ")
                card_data = {"card_data": card_data_input}

                await websocket.send(json.dumps(card_data))

                # Recibe y muestra la respuesta del servidor
                response = await websocket.recv()
                print(f"Respuesta del servidor: {response}")
    except websockets.exceptions.ConnectionClosedError as e:
        print("SERVER ERROR")
    except websockets.exceptions.ConnectionClosed as e:
        print("ERROR: CONNECTION CLOSED")
    except Exception as e:
        print(f"ERROR: SERVER CAN NOT FOUND")

asyncio.get_event_loop().run_until_complete(simulate_rfid_card())
