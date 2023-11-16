# client.py
import asyncio
import websockets
import json
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

async def simulate_rfid_card():
    try:
        async with websockets.connect("ws://localhost:8077") as websocket:
            while True:
                reader = SimpleMFRC522()
                try:
                        id, text = reader.read()
                finally:
                        GPIO.cleanup()
                await websocket.send(json.dumps(text))

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
