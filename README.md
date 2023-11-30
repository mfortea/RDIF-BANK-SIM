# 💳 RFID SECURITY PROJECT
Project about use of RFID cards (securized) for the course Computer System Security of the HMU (Hellenic Mediterranean University).

Requirements:
- Pyhton 3.6 or later
- Library Asyncio
- Library Websockets
- Library JSON
- Library Dotenv
- MFRC 522 Drivers/Library


## 📚 Libraries installation: 
```
pip3 install asyncio websocket-client os dotenv load_dotenv
```


## 🚀 For run the server:
```
python3 server.py
```


## 👨🏻‍💻 For the client, run:
```
python3 client.py
```

## 📄 Enviroment file format
```
WEBSOCKET_SERVER=localhost
WEBSOCKET_PORT=8078
SERVER_MODE=localhost
SIMULATION=True
CERT_PATH=cert.pem
KEY_PATH=key.pem

```

## 🔒 SECURITY
- Base64 for the data manipulation
- SSL/TLS for the client-server communication
- Bcrypt for hashing the passwords
