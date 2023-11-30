import asyncio
import websockets
import json
from dotenv import load_dotenv
import subprocess
import os
import ssl
import base64

def clear_terminal():
    if os.name == 'nt':
        subprocess.run('cls', shell=True)
    else:
        subprocess.run('clear', shell=True)

async def pause():
    await asyncio.sleep(1)

clear_terminal()
current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_directory)
grandparent_directory = os.path.dirname(parent_directory)
env_file_path = os.path.join(grandparent_directory, '.env')
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
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations(CERT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def read_card_data(prompt_message):
    if SIMULATION:
        return input(prompt_message)
    else:
        print(prompt_message)
        data = reader.read()
        card_data = data[1]
        GPIO.cleanup()
        return card_data
    
async def client_process(websocket):
    print("\nSYSTEM LOGIN")
    print("-> USER AUTHENTICATION: ")
    user_card = read_card_data("Please approach your User Card to the reader...")
    await websocket.send(json.dumps({"user_card": user_card}))

    user_check_response = await websocket.recv()
    if user_check_response != "USER_OK":
        print(f"\nAccess Denied: {user_check_response}")
        return
    else:
        print("User verified successfully.")

    print("\n-> AUTHENTICATION CARD: ")
    auth_card = read_card_data("Please approach your Auth Card to the reader...")
    await websocket.send(json.dumps({"auth_card": auth_card}))

    auth_response = await websocket.recv()
    if auth_response != "AUTH_OK":
        print(f"\nAuthentication failed: {auth_response}")
        return
    
    print("AUTHENTICATION CARD OK!")

    while True:
        print("\n||== MAIN MENU ==||")
        print("1. View Real-Time Information")
        print("2. Open Doors")
        print("3. Close Doors")
        choice = input("Enter your choice: ")
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
