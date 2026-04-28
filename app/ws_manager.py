from fastapi import WebSocket
from typing import Dict
from app.database import db_conn
from app.security import encrypt_message, decrypt_message

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        print(f"[online]  {username}")

        # Доставка офлайн-сообщений
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT id, sender, ciphertext FROM offline_messages WHERE receiver = ?",
            (username,)
        )
        rows = cursor.fetchall()
        for msg_id, sender, ciphertext in rows:
            try:
                text = decrypt_message(ciphertext)
            except Exception:
                text = "[не удалось расшифровать сообщение]"
            await websocket.send_json({"from": sender, "text": text, "queued": True})
            cursor.execute("DELETE FROM offline_messages WHERE id = ?", (msg_id,))
        if rows:
            db_conn.commit()

    def disconnect(self, username: str):
        self.active_connections.pop(username, None)
        print(f"[offline] {username}")

    async def send_message(self, text: str, receiver: str, sender: str):
        if receiver in self.active_connections:
            await self.active_connections[receiver].send_json(
                {"from": sender, "text": text, "queued": False}
            )
        else:
            cursor = db_conn.cursor()
            cursor.execute(
                "INSERT INTO offline_messages (sender, receiver, ciphertext) VALUES (?, ?, ?)",
                (sender, receiver, encrypt_message(text))
            )
            db_conn.commit()

manager = ConnectionManager()