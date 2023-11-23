import asyncio
import websockets
import json
from dotenv import load_dotenv
import subprocess
import os

def clear_terminal():
    # Windows
    if os.name == 'nt':
        subprocess.run('cls', shell=True)
    # Unix/Linux/MacOS
    else:
        subprocess.run('clear', shell=True)

clear_terminal()

# Loading variables from .env
load_dotenv()

SIMULATION = os.getenv("SIMULATION") == 'True'

if not SIMULATION:
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()

SERVER_IP = os.getenv("WEBSOCKET_SERVER")
PORT = os.getenv("WEBSOCKET_PORT")

websockets_ip = "ws://" + SERVER_IP + ":" + PORT

async def client_process(websocket):
    try:
        while True:
            print("\n||== BANK TRANSACTION SIMULATOR ==||")

            # Validating amount input
            while True:
                amount = input("\n-> Please enter the amount to pay: ")
                if amount.isdigit():
                    break
                print("Please enter a valid number for the amount.")

            # Getting card data
            if SIMULATION:
                while True:
                    card_data = input("\nSIMULATION: Enter your RFID card data: ")
                    print("# Card found")
                    if len(card_data.encode('utf-8')) <= 48:
                        break
                    print("Card data cannot exceed 48 characters")
            else:
                print("Please approach your RFID card to the reader...")
                data = reader.read()
                card_data = data[1]
                print("# Card found")
                GPIO.cleanup()
                if len(card_data.encode('utf-8')) > 48:
                    print("Error: Card data exceeds 48 characters")
                    continue

            payment_data = {"amount": amount, "card_data": card_data}
            await websocket.send(json.dumps(payment_data))

            # Receiving and displaying server response
            response = await websocket.recv()
            print(f"\n-> SERVER RESPONSE: {response}")
            input("\nPress enter for make another transaction... ")
            clear_terminal()
    except Exception as e:
        print(f"ERROR: {e}")

async def main():
    async with websockets.connect(websockets_ip) as websocket:
        print("*** Connected to the server successfully ***")
        await client_process(websocket)

asyncio.get_event_loop().run_until_complete(main())
