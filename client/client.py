import asyncio
import websockets
import json
from dotenv import load_dotenv
import subprocess
import os
import ssl
import base64
import sys
import termios
import tty

def get_key():
    fd = sys.stdin.fileno()
    original_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_settings)
    return ch

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
    
async def manage_users(websocket):
    while True:
        print("\n||== USER MANAGEMENT MENU ==||")
        print("\n1. List Users")
        print("2. Modify User")
        print("3. Delete User")
        print("4. Add User")
        print("\nPress ESCAPE for return to Main Menu")
        print("\n-> Enter your choice: ")

        choice = get_key()

        if choice == '\x1b':  # ASCII code for ESC
            break 
        elif choice == "1":
            await websocket.send("list_users")
            users = await websocket.recv()
            print("Users:", json.loads(users))
        elif choice == "2":
            username = input("Enter username to modify: ")
            new_status = input("Enter new status (enable/disable): ")
            await websocket.send(f"modify_user {username} {new_status}")
            response = await websocket.recv()
            print(response)
        elif choice == "3":
            username = input("Enter username to delete: ")
            await websocket.send(f"delete_user {username}")
            response = await websocket.recv()
            print(response)
        elif choice == "4":
            new_user = input("Enter new username: ")
            is_boss = input("Is the user a boss? (yes/no): ").lower() == 'yes'
            is_enabled = input("Should the user be enabled? (yes/no): ").lower() == 'yes'
            await websocket.send(f"add_user {new_user} {'yes' if is_boss else 'no'} {'yes' if is_enabled else 'no'}")
            response = await websocket.recv()
            print(response)
        else:
            print("Invalid option")

async def client_process(websocket, is_boss):
    while True:
        print("\nSYSTEM LOGIN")
        print("-> USER AUTHENTICATION: ")
        user_card = read_card_data("Please approach your User Card to the reader...")
        await websocket.send(json.dumps({"user_card": user_card}))

        user_check_response = await websocket.recv()
        if "USER_OK" not in user_check_response:
            print(f"\nAccess Denied: {user_check_response}")
            print("Please approach your User Card to the reader again...")
            continue
        else:
            _, boss_status = user_check_response.split(';')
            is_boss = boss_status == 'boss'
            print("User verified successfully.")

        print("\n-> AUTHENTICATION CARD: ")
        auth_card = read_card_data("Please approach your Auth Card to the reader...")
        await websocket.send(json.dumps({"auth_card": auth_card}))

        auth_response = await websocket.recv()
        if auth_response != "AUTH_OK":
            print(f"\nAuthentication failed: {auth_response}")
            return
        break
    print("AUTHENTICATION CARD OK!")

    while True:
            try:
                print("\n||== MAIN MENU ==||")
                print("\n1. View Real-Time Information")
                print("2. Open Doors")
                print("3. Close Doors")
                if is_boss:
                    print("4. Manage Users")
                print("\nPress ESCAPE for disconnet")
                print("\n-> Enter your choice: ")

                choice = get_key()

                if choice == '\x1b':  # ASCII code for ESC
                    break 
                elif choice == "1":
                    clear_terminal()
                    print("Option under development...")
                elif choice == "2":
                    clear_terminal()
                    print("Option under development...")
                elif choice == "3":
                    clear_terminal()
                    print("Option under development...")
                elif choice == "4" and is_boss:
                    clear_terminal()
                    await manage_users(websocket)
                else:
                    print("Invalid option")

                input("Press enter for continue... ")
                clear_terminal()

            except websockets.exceptions.ConnectionClosed:
                clear_terminal()
                print("SERVER DISCONNECTED")
                break
            except Exception as e:
                clear_terminal()
                print(f"Error: {e}")

async def main():
    try:
        async with websockets.connect(websockets_ip, ssl=ssl_context) as websocket:
            print("*** Connected to the server successfully ***")
            is_boss = False
            await client_process(websocket, is_boss)
    except (ConnectionRefusedError, OSError):
        print("\nSERVER NOT FOUND")
    except websockets.exceptions.ConnectionClosed:
        print("\nSERVER DISCONNECTED")
    except KeyboardInterrupt:
        print("\n\nCLIENT CLOSED")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
