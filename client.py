# client.py
import asyncio
import websockets
import json
from dotenv import load_dotenv 
import os
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

# Loading variables from .env
load_dotenv()

SERVER_IP = os.getenv("WEBSOCKET_SERVER")
PORT = os.getenv("WEBSOCKET_PORT")
SIMULATION = os.getenv("SIMULATION")

websockets_ip="ws://"+SERVER_IP+":"+PORT

async def simulate_rfid_card():
    try:
        async with websockets.connect(websockets_ip) as websocket:
            while True:
                print("WAITING FOR RDIF CARD...")
                data_array = reader.read()
                print(data_array[1])
                card_data = data_array[1]
                GPIO.cleanup()
                await websocket.send(json.dumps(card_data))
                # Recibe y muestra la respuesta del servidor
                response = await websocket.recv()
                print(f"SERVER RESPONSE: {response}")
    except websockets.exceptions.ConnectionClosedError as e:
        print("SERVER ERROR")
    except websockets.exceptions.ConnectionClosed as e:
        print("ERROR: CONNECTION CLOSED")
    except Exception as e:
        print(e)

asyncio.get_event_loop().run_until_complete(simulate_rfid_card())