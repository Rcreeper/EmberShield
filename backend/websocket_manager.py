"""
EmberShield WebSocket Manager

This module manages all connected frontend clients and broadcasts
real-time reasoning updates from the AI agents.

Every step performed by Sentinel, Risk Analyst and Commander is
sent instantly to the frontend, allowing users to watch the AI
reason in real time.
"""

from fastapi import WebSocket
from typing import List
import json


class ConnectionManager:
    """
    Manages active websocket connections.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept a new websocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a disconnected websocket.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, agent: str = "System"):
        """
        Broadcast a reasoning update to every connected client.
        """

        payload = {
            "agent": agent,
            "message": message
        }

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                disconnected.append(connection)

        # Clean up broken connections
        for connection in disconnected:
            self.disconnect(connection)

    async def send_progress(
        self,
        current: int,
        total: int,
        message: str,
        agent: str = "System"
    ):
        """
        Broadcast progress updates.
        Useful for multi-hotspot processing.
        """

        payload = {
            "agent": agent,
            "message": message,
            "progress": {
                "current": current,
                "total": total
            }
        }

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


# Singleton manager used throughout the backend
manager = ConnectionManager()