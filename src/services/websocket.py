import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        # send to all connected frontends
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


manager = ConnectionManager()
