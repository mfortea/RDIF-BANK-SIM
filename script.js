let ws;

function initWebSocket() {
    ws = new WebSocket('ws://localhost:8077');

    ws.onopen = function(event) {
        updateStatus("Connected to the server.");
    };

    ws.onmessage = function(event) {
        updateStatus(`${event.data}`);
    };

    ws.onerror = function(event) {
        updateStatus("Connection error.");
    };

    ws.onclose = function(event) {
        updateStatus("Connection closed.");
    };
}

function updateStatus(message) {
    document.getElementById('status').innerText = message;
}

window.onload = initWebSocket;
