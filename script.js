// script.js
let ws;
let isConnected = false;
let amount = 0;

let server_ip = "localhost";
let server_port = 8078;

function initWebSocket() {
    ws = new WebSocket('ws://'+ server_ip + ':'+ server_port);

    ws.onopen = function(event) {
        updateConnectionStatus(true);
    };

    ws.onmessage = function(event) {
        updateStatus(event.data);
    };

    ws.onerror = function(event) {
        updateConnectionStatus(false);
    };

    ws.onclose = function(event) {
        updateConnectionStatus(false);
    };
}

function updateConnectionStatus(connected) {
    isConnected = connected;
    const statusText = connected ? "Connected ✅" : "Disconnected ❌";
    document.getElementById('connectionStatus').innerText = "Server Status: " + statusText;
    updateKeypadEnabled(connected);
}

function updateKeypadEnabled(enabled) {
    const buttons = document.querySelectorAll('.keypadButton, #okButton, #clearButton');
    buttons.forEach(button => {
        button.disabled = !enabled;
        button.style.backgroundColor = enabled ? '' : 'grey';
    });
}

function updateStatus(message) {
    document.getElementById('status').innerText = message;
}


function pressKey(key) {
    if (key === 'clear') {
        amount = 0;
    } else {
        amount = amount * 10 + parseInt(key, 10);
    }
    document.getElementById('amountDisplay').innerText = amount + ' €';
}

function processPayment() {
    // Enviar la cantidad al servidor
    ws.send(JSON.stringify({ amount: amount }));
    amount = 0;
    document.getElementById('amountDisplay').innerText = amount + ' €';
    document.getElementById('status').innerText = '💳 Put your RFID card, please.';
}

window.onload = initWebSocket;
