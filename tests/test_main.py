import pytest
from fastapi.testclient import TestClient
from main import app, messages, websockets

client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Local Chat" in response.text
    assert "ws://192.168.1.100:8000/ws" in response.text

def test_send_message():
    response = client.post("/send-message/", data={"message": "Test message"})
    assert response.status_code == 200
    assert response.json() == {"status": "message sent"}
    assert "Test message" in messages

@pytest.mark.asyncio
async def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("Hello, WebSocket!")
        data = websocket.receive_text()
        assert data == "Hello, WebSocket!"
        assert len(websockets) == 1

@pytest.mark.asyncio
async def test_multiple_websockets():
    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2:
        ws1.send_text("Message from WS1")
        data = ws2.receive_text()
        assert data == "Message from WS1"
        assert len(websockets) == 2

def test_websocket_disconnect():
    with client.websocket_connect("/ws") as websocket:
        pass
    assert len(websockets) == 0

def test_send_message_to_multiple_clients():
    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2:
        response = client.post("/send-message/", data={"message": "Broadcast message"})
        assert response.status_code == 200
        assert ws1.receive_text() == "Broadcast message"
        assert ws2.receive_text() == "Broadcast message"
