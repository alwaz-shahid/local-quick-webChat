import socket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI()

messages: List[str] = []
websockets: List[WebSocket] = []

class Message(BaseModel):
    message: str

def get_local_ip() -> str:
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except Exception as e:
        local_ip = f"Unable to determine local IP: {e}"
    return local_ip

@app.get("/", response_class=HTMLResponse)
async def index():
    local_ip = get_local_ip()  # Get the local IP address
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Chat</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.3.1/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 p-6">
    <h1 class="text-3xl font-bold mb-4">Local Chat</h1>
    <p class="mb-4">Your local IP address is: <span id="local-ip" class="font-mono">{local_ip}</span></p>
    <form id="message-form" class="mb-4">
        <input type="text" id="message" name="message" class="border p-2 rounded" required>
        <button type="submit" class="bg-blue-500 text-white p-2 rounded">Send</button>
    </form>
    <div id="messages" class="bg-white p-4 border rounded">
        <ul id="message-list">
            <!-- Message items will be injected here -->
        </ul>
    </div>
    <script>
        document.getElementById('message-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const messageInput = document.getElementById('message');
            const message = messageInput.value;

            fetch('/send-message/', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ message: message }})
            }}).then(response => {{
                if (response.ok) {{
                    messageInput.value = ''; // Clear the input field
                }} else {{
                    console.error('Error:', response.statusText);
                }}
            }}).catch(error => console.error('Error:', error));
        }});

        var ws = new WebSocket('ws://' + window.location.host + '/ws');
        ws.onmessage = function(event) {{
            var messages = document.getElementById('message-list');
            var messageItem = document.createElement('li');
            messageItem.textContent = event.data;
            messages.appendChild(messageItem);
        }};
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/send-message/")
async def send_message(msg: Message):
    messages.append(msg.message)
    for websocket in websockets:
        await websocket.send_text(msg.message)
    return {"status": "message sent"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            messages.append(data)
            for ws in websockets:
                if ws != websocket:
                    await ws.send_text(data)
    except WebSocketDisconnect:
        websockets.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
