# client.py
import asyncio
import websockets
import json
from dotenv import load_dotenv 
import os
import platform

if platform.system() == 'Linux':
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
else:
    print("This code requires a Raspberry Pi for the library RPi.GPIO.")


# Loading variables from .env
load_dotenv()

SERVER_IP = os.getenv("WEBSOCKET_SERVER")
PORT = os.getenv("WEBSOCKET_PORT")
SIMULATION = os.getenv("SIMULATION")


websockets_ip="ws://"+SERVER_IP+":"+PORT


async def simulate_rfid_card():
    try:
        async with websockets.connect(websockets_ip) as websocket:
            reader = SimpleMFRC522()
            try:
                text = reader.read()
            finally:
                GPIO.cleanup()
                await websocket.send(json.dumps(text))

        response = await websocket.recv()
        print(f"Respuesta del servidor: {response}")
    except websockets.exceptions.ConnectionClosedError as e:
        print("SERVER ERROR")
    except websockets.exceptions.ConnectionClosed as e:
        print("ERROR: CONNECTION CLOSED")
    except Exception as e:
        print(e)

asyncio.get_event_loop().run_until_complete(simulate_rfid_card())
