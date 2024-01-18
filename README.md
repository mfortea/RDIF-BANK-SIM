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


## 🌏 For the web client, run:
For install the requires JS modules
```
npm i
```
For run the app
```
node app.js
```
This initiates the web client, that show the actual price of the "gas station simulator"

## 🔒 SECURITY
- AES encryption for sensitive data.
- SSL/TLS for secure client-server communication.
- Secure handling of user passwords and RFID card data.
- Real-time price administration with secure database transactions.
- Nonce usage for preventing replay attacks.

## 📄 Enviroment files format

For server.py & card_creator.py
```
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_NAME=
SIMULATION=
```


For client.py
```
SERVER_IP=
SERVER_PORT=
SIMULATION=
```


For the web client
```
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=
SERVER_PORT=
```



