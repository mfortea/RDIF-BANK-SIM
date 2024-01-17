# CLIENT.PY

import os
import websocket
import json
import ssl
import dotenv
import time
import signal
import sys

def signal_handler(sig, frame):
    print('\nClosing WebSocket connection...')
    ws.close()
    print('Connection closed. Exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Cargar variables de entorno desde .env.client
dotenv.load_dotenv('.env_client')

# Variables de entorno
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")

simulation_mode = os.getenv("SIMULATION", "False").lower() == "true"
username = None

def clear_screen():
    # Comando para Windows
    if os.name == 'nt':
        os.system('cls')
    # Comando para Unix/Linux/Mac
    else:
        os.system('clear')

# Llamar a clear_screen al inicio
clear_screen()
print("CLIENT RUNNING...\n")

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### Connection closed ###")
    if close_status_code or close_msg:
        print("### Connection closed ###")

def read_data_from_cards(simulation):
    if simulation:
        # Leer datos de archivos de simulación
        card_data = []
        for i in range(4):
            with open(f"card_{i}.txt", "r") as file:
                card_data.append(file.read().strip())
        return card_data  
    else:
        # Leer datos de las tarjetas RFID reales
        from mfrc522 import SimpleMFRC522
        import RPi.GPIO as GPIO
        GPIO.setwarnings(False)
        reader = SimpleMFRC522()
        try:
            card_data = []
            for i in range(4):
                print(f"\nApproach card {i + 1} to the RFID reader...")
                id, data = reader.read()
                card_data.append(data.strip())
                print(f"-> Card {i + 1} read || Please, remove the card")
                time.sleep(2)
            return card_data
        finally:
            GPIO.cleanup()

def send_card_data_to_server(ws, card_data, username):
        # Empaquetar los datos en un objeto JSON y enviarlos al servidor
        message = json.dumps({
        'username': username,
        'aes_key': card_data[0] + card_data[1],
        'card_nonce': card_data[2],
        'card_encrypted_password_hex': card_data[3]
        })
        ws.send(message)

def on_open(ws):
    global username
    print("Connecting to server ...")
    username = input("Enter username: ")
    print("Sending username ...")
    ws.send(json.dumps({'type': 'username', 'data': username}))


def on_message(ws, message):
    global username
    response = json.loads(message)
    response_type = response.get('type')

    if response_type == 'error':
        print(response.get('data'))
        if "exceeded" in response.get('data').lower():
            print("Closing connection...")
            ws.close()
        elif "format" in response.get('data').lower():
            user_input = input("Enter the value: ")
            ws.send(json.dumps({'type': 'input_response', 'data': user_input}))
        else:
            print("Unhandled error. Closing connection...")
            ws.close()
    elif response_type == 'request_cards':
        print("Sending card data ...")
        card_data = read_data_from_cards(simulation_mode)
        send_card_data_to_server(ws, card_data, username)
    elif response_type == 'menu' or response_type == 'input':
        print(response.get('data'))
        user_input = input("Your choice: " if response_type == 'menu' else "Enter the value: ")
        ws.send(json.dumps({'type': 'choice' if response_type == 'menu' else 'input_response', 'data': user_input}))
    else:
        print(response.get('data'))


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f"wss://{SERVER_IP}:{SERVER_PORT}",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    # Configuración para SSL y ping/pong
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, 
                   ping_interval=290,
                   ping_timeout=10)   
