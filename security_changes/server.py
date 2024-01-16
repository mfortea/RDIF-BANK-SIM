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

# Cargar variables de entorno
dotenv.load_dotenv('.env.server')

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

# Funciones para manejar eventos de WebSocket
def new_client(client, server):
    print("Nuevo cliente conectado y fue dado id %d" % client['id'])
    server.send_message_to_all("Hey all, a new client has joined us")

def client_left(client, server):
    print("Cliente(%d) desconectado" % client['id'])

def message_received(client, server, message):
    # Aquí se manejarán los mensajes recibidos
    pass

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

async def authenticate_user(data):
    try:
        # Conectar a la base de datos
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()

        # Descomponer los datos recibidos
        username, aes_key, card_nonce, card_encrypted_password_hex = data
        cursor.execute("SELECT password, nonce FROM users WHERE username=?", (username,))
        print("HE RECIBIDO EL USUARIO: ", {username})
        user_data = cursor.fetchone()

        if not user_data:
            return False, "Username doesn't exist."

        stored_encrypted_password_hex, stored_nonce_hex = user_data
        stored_nonce = bytes.fromhex(stored_nonce_hex)

        if bytes.fromhex(card_nonce) != stored_nonce:
            return False, "Nonce mismatch."

        aes_key = bytes.fromhex(aes_key)
        card_encrypted_password = bytes.fromhex(card_encrypted_password_hex)

        # Desencriptar contraseña
        decrypted_password_bytes = decrypt_aes(card_encrypted_password, aes_key, stored_nonce)

        # Comparar hashes de contraseñas
        decrypted_password_hash = hashlib.sha256(decrypted_password_bytes).hexdigest()
        is_valid = decrypted_password_hash == stored_encrypted_password_hex

        return is_valid, "Access Granted!" if is_valid else "Access Denied"

    finally:
        conn.close()

async def handler(websocket, path):
    try:
        print("Cliente conectado. Esperando nombre de usuario...")
        # Recibir el nombre de usuario
        username_message = await websocket.recv()
        username_data = json.loads(username_message)
        username = username_data.get('data')

        # Verificar si el usuario existe en la base de datos
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM users WHERE username=?", (username,))
        if cursor.fetchone()[0] == 0:
            await websocket.send(json.dumps({'type': 'error', 'data': 'Usuario no existe.'}))
            return
        else:
            await websocket.send(json.dumps({'type': 'request_cards', 'data': 'Por favor, envíe los datos de las tarjetas.'}))

        # Esperar los datos de las tarjetas
        print("Esperando datos de las tarjetas...")
        card_data_message = await websocket.recv()
        card_data = json.loads(card_data_message)

        # Autenticar al usuario
        is_valid, response = await authenticate_user(card_data)

        # Enviar respuesta al cliente
        await websocket.send(json.dumps({'type': 'auth_result', 'data': response}))
    except websockets.exceptions.ConnectionClosedError:
        print("Conexión cerrada inesperadamente.")



# Crear un servidor WebSocket
start_server = websockets.serve(handler, '0.0.0.0', 8001, ssl=context)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
