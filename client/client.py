import asyncio
import websockets
import json
from dotenv import load_dotenv
import subprocess
import os
import ssl
import base64
import hashlib
import getpass

def clear_terminal():
    # Clear the terminal screen
    if os.name == 'nt':
        subprocess.run('cls', shell=True)
    else:
        subprocess.run('clear', shell=True)

clear_terminal()

# Load environment variables
current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_directory)
env_file_path = os.path.join(parent_directory, '.env')
load_dotenv(env_file_path)

SIMULATION = os.getenv("SIMULATION") == 'True'
SERVER_IP = os.getenv("WEBSOCKET_SERVER")
PORT = os.getenv("WEBSOCKET_PORT")
CERT = os.getenv("CERT_PATH")

if not SIMULATION:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()

websockets_ip = "wss://" + SERVER_IP + ":" + PORT

# Configure SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations(CERT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def encrypt_credentials(username):
    return base64.b64encode(username.encode()).decode()

def read_card_data(prompt_message):
    if SIMULATION:
        return input(prompt_message)
    else:
        print("\nPlease approach your RFID card to the reader...")
        id, card_data = reader.read()
        GPIO.cleanup()
        return card_data

async def client_process(websocket):
    print("\SYSTEM LOGIN")
    user_card = read_card_data("-> USER AUTHENTICATION: ")
    auth_card = read_card_data("-> AUTHENTICATION CARD: ")

    encrypted_user_card = encrypt_credentials(user_card)
    encrypted_auth_card = encrypt_credentials(auth_card)
    await websocket.send(json.dumps({"user_card": encrypted_user_card, "auth_card": encrypted_auth_card}))

    auth_response = await websocket.recv()
    if auth_response != "AUTH_OK":
        print(f"\nAuthentication failed: {auth_response}")
        return

    # Main menu
    while True:
        print("\n||== MAIN MENU ==||")
        print("1. View Real-Time Information")
        print("2. Open Doors")
        print("3. Close Doors")
        choice = input("Enter your choice: ")
        # Send choice to server (implementation pending)
        # await websocket.send(json.dumps({"choice": choice}))
        print("Option under development...")
        input("Press enter to return to the main menu... ")
        clear_terminal()

async def main():
    try:
        async with websockets.connect(websockets_ip, ssl=ssl_context) as websocket:
            print("*** Connected to the server successfully ***")
            await client_process(websocket)
    except (ConnectionRefusedError, OSError):
        print("\nSERVER NOT FOUND")
    except KeyboardInterrupt:
        print("\n\nCLIENT CLOSED")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
