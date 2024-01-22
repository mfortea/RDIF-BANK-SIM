# SERVER.PY

import os
import dotenv
import mariadb
import ssl
import asyncio
import websockets
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import re
import signal
import websockets.exceptions
from cryptography.fernet import Fernet
import getpass
from cryptography.fernet import Fernet
import base64
import getpass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


async def shutdown(signal, loop):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

# Cargar variables de entorno
dotenv.load_dotenv('.env')

# Configuración de la base de datos y otras variables de entorno
db_config = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'database': os.getenv("DB_NAME")
}

# Configuración SSL
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

def clear_screen():
    # Comando para Windows
    if os.name == 'nt':
        os.system('cls')
    # Comando para Unix/Linux/Mac
    else:
        os.system('clear')

clear_screen()
print("SERVER RUNNING...\n")


# Funciones para manejar eventos de WebSocket
def new_client(client, server):
    print("Nuevo cliente conectado y fue dado id %d" % client['id'])
    server.send_message_to_all("Hey all, a new client has joined us")

def client_left(client, server):
    print("Client(%d) disconnected" % client['id'])

def message_received(client, server, message):
    # Aquí se manejarán los mensajes recibidos
    pass

def decrypt_key(encrypted_key, password):
    f = Fernet(password)
    return f.decrypt(encrypted_key)

def derive_fernet_key(password: bytes, salt: bytes):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def derive_diversified_key(master_key, user_id):
    combined = master_key + user_id.encode()
    return hashlib.sha256(combined).digest()

def read_master_key():
    with open("master_key_encrypted", "rb") as key_file:
        salt, encrypted_key = key_file.read().split(b' ')
    password = getpass.getpass("Input password for Master Key: ").encode()
    password_key = derive_fernet_key(password, salt)
    
    f = Fernet(password_key)
    return f.decrypt(encrypted_key)

# Función para desencriptar los datos
def decrypt_aes(encrypted_data, key, nonce):
    if isinstance(encrypted_data, str):
        encrypted_data = bytes.fromhex(encrypted_data)
    if isinstance(key, str):
        key = bytes.fromhex(key)
    if isinstance(nonce, str):
        nonce = bytes.fromhex(nonce)

    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()

def derive_diversified_key(master_key, user_id):
    combined = master_key + user_id.encode()
    return hashlib.sha256(combined).digest()



async def authenticate_user(data, master_key):
    conn = None
    try:
        username = data.get('username')
        diversified_key = derive_diversified_key(master_key, username)
        # Conectar a la base de datos
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()

        # Descomponer los datos recibidos
       
        aes_key_hex = data.get('aes_key') ## IT IS NOT ACTUALLY THE AES_KEY. ITS THE DIVERSIFIED KEY
        card_nonce_hex = data.get('card_nonce')
        card_encrypted_password_hex = data.get('card_encrypted_password_hex')

        # Convertir de hex a bytes si los datos son cadenas
        aes_key = bytes.fromhex(aes_key_hex) if isinstance(aes_key_hex, str) else aes_key_hex
        card_nonce = bytes.fromhex(card_nonce_hex) if isinstance(card_nonce_hex, str) else card_nonce_hex
        card_encrypted_password = bytes.fromhex(card_encrypted_password_hex) if isinstance(card_encrypted_password_hex, str) else card_encrypted_password_hex

        # Comprobar si el usuario existe en la base de datos
        cursor.execute("SELECT password, nonce FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()

        if not user_data:
            return False, "Username doesn't exist."

        # Comparar el nonce y desencriptar la contraseña
        stored_encrypted_password_hex, stored_nonce_hex = user_data
        stored_nonce = bytes.fromhex(stored_nonce_hex) if isinstance(stored_nonce_hex, str) else stored_nonce_hex

        if card_nonce != stored_nonce:
            return False, "Nonce mismatch."

        # Desencriptar contraseña
        decrypted_password_bytes = decrypt_aes(card_encrypted_password, diversified_key, card_nonce)

        # Comparar hashes de contraseñas
        decrypted_password_hash = hashlib.sha256(decrypted_password_bytes).hexdigest()
        is_valid = decrypted_password_hash == stored_encrypted_password_hex

        return is_valid, "\nAccess Granted! Welcome" if is_valid else "Access Denied"

    finally:
        if conn is not None:
            conn.close()

def get_current_prices():
    try:
        # Conectar a la base de datos
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()

        # Obtener los precios actuales
        cursor.execute("SELECT gasoline_price, diesel_price FROM prices WHERE id = 1")
        prices = cursor.fetchone()

        return {
            'gasoline_price': prices[0] if prices else 'Unavailable',
            'diesel_price': prices[1] if prices else 'Unavailable'
        }

    except mariadb.Error as e:
        print(f"Error retrieving prices: {e}")
        return {'gasoline_price': 'Error', 'diesel_price': 'Error'}
    finally:
        conn.close()


async def show_menu_and_process_choice(websocket, username):
    while True:         
        current_prices = get_current_prices()
        prices_info = f"\n** PRICES ADMINISTRATION ** \nCurrent Gasoline Price: {current_prices['gasoline_price']}\nCurrent Diesel Price: {current_prices['diesel_price']}"

        # Construir y enviar el menú
        menu = f"{prices_info}\n\n1) Change Gasoline Price\n2) Change Diesel Price\n0) Exit"
        await websocket.send(json.dumps({'type': 'menu', 'data': menu}))

        choice_message = await websocket.recv()
        choice = json.loads(choice_message).get('data')

        if choice == '1':
            await change_price(websocket, "gasoline_price")
        elif choice == '2':
            await change_price(websocket, "diesel_price")
        elif choice == '0':
            await websocket.send(json.dumps({'type': 'info', 'data': 'Exiting...'}))
            break  # Salir del bucle y finalizar la función
        else:
            await websocket.send(json.dumps({'type': 'error', 'data': 'Invalid choice.'}))

    # Cerrar la conexión después de salir del menú
    await websocket.close()


async def change_price(websocket, price_type):
    fuel_type = ''
    if price_type == 'gasoline_price':
        fuel_type = 'gasoline'
    elif price_type == 'diesel_price':
        fuel_type = 'diesel'
    await websocket.send(json.dumps({'type': 'input', 'data': f"\nEnter new {fuel_type} price (format 00,00):"}))

    # Esperar el nuevo precio
    new_price_message = await websocket.recv()
    new_price = json.loads(new_price_message).get('data')

    # Validar y actualizar el precio
    if is_valid_price_format(new_price):
        update_price_in_db(price_type, new_price)
        await websocket.send(json.dumps({'type': 'info', 'data': f'\n-> The new {fuel_type} price is {new_price}.'}))
        await show_menu_and_process_choice(websocket, username_gen)
    else:
        await websocket.send(json.dumps({'type': 'error', 'data': '\nInvalid price format.'}))
        # Volver a pedir el precio
        await change_price(websocket, price_type)


def is_valid_price_format(price_str):
    return re.match(r"^\d{1,2}[.,]\d{1,2}$", price_str)

def update_price_in_db(price_type, new_price):
    try:
        # Conectar a la base de datos
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()

        # Reemplazar comas por puntos y convertir a decimal
        formatted_price = float(new_price.replace(',', '.'))
        
        # Asegurarse de que el precio cumple con el formato decimal(5,2)
        if formatted_price >= 0 and formatted_price < 1000:
            cursor.execute(f"UPDATE prices SET {price_type} = %s WHERE id = 1", (formatted_price,))
            conn.commit()
        else:
            print(f"Error: The price {formatted_price} has an invalid format.")
            return

    except mariadb.Error as e:
        print(f"Error updating {price_type}: {e}")
    finally:
        conn.close()


async def handler(websocket, path):
    global username_gen  
    try:
        attempts = 0
        while attempts < 3:
            print("Client Connected. Waiting for login...")
            # Recibir el nombre de usuario
            username_message = await websocket.recv()
            username_data = json.loads(username_message)
            username = username_data.get('data')
            username_gen = username

            # Verificar si el usuario existe en la base de datos
            conn = mariadb.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(1) FROM users WHERE username=?", (username,))
            if cursor.fetchone()[0] == 0:
                await websocket.send(json.dumps({'type': 'error', 'data': 'User does not exist. Try again.'}))
                attempts += 1
            else:
                await websocket.send(json.dumps({'type': 'request_cards', 'data': 'Please, send card data'}))

                # Esperar los datos de las tarjetas
                print("Waiting for card data...")
                card_data_message = await websocket.recv()
                card_data = json.loads(card_data_message)

                # Autenticar al usuario
                is_valid, response = await authenticate_user(card_data, master_key)
                print(f"\nUser {username} is now logged in")
                # Enviar respuesta al cliente
                await websocket.send(json.dumps({'type': 'auth_result', 'data': response}))
                if is_valid:
                    await show_menu_and_process_choice(websocket, username)
                break

        if attempts >= 2:
            await websocket.send(json.dumps({'type': 'error', 'data': 'Maximum login attempts exceeded.'}))

    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed unexpectedly.")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Leer y descifrar la clave maestra
    global master_key
    master_key = read_master_key()
    print("\n** SERVER STARTED **")

    loop = asyncio.get_event_loop()
    # Registrar el manejador de señales para SIGINT (Control+C)
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown(signal.SIGINT, loop)))

    # Iniciar el servidor WebSocket
    start_server = websockets.serve(
        handler,
        '0.0.0.0',
        8001,
        ssl=context,
        ping_interval=290,
        ping_timeout=10
    )
    loop.run_until_complete(start_server)

    try:
        loop.run_forever()
    finally:
        loop.close()
        print("\n**SERVER CLOSED**")