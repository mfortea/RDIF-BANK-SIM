# 💳 RFID SECURITY PROJECT
Project utilizing RFID cards for secure authentication, with real-time price administration functionality. Developed for the Computer System Security course at the Hellenic Mediterranean University.

## Requirements
- Python 3.6 or later
- Libraries: Asyncio, Websockets, JSON, Dotenv
- MFRC 522 Drivers/Library (for RFID functionality)
- MariaDB (for database operations)
- Cryptography Library (for AES encryption)

## 📚 Libraries Installation
```bash
pip3 install asyncio websocket-client os dotenv cryptography mariadb
```

## 🚀 For run the server:
```
python3 server.py
```
This command starts the server, which handles user authentication, price administration, and secure WebSocket communication.

## 👨🏻‍💻 For the client, run:
```
python3 client.py
```
This initiates the client-side application, allowing users to log in using RFID cards and interact with the server to administer prices.

## 🔒 SECURITY
- AES encryption for sensitive data.
- SSL/TLS for secure client-server communication.
- Secure handling of user passwords and RFID card data.
- Real-time price administration with secure database transactions.
- Nonce usage for preventing replay attacks.

## 📄 Enviroment file format
```
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=host_address
DB_NAME=database_name
SIMULATION=True_or_False
SERVER_IP=websocket_server_ip
SERVER_PORT=websocket_server_port
CERT_PATH=path_to_cert.pem
KEY_PATH=path_to_key.pem
```




