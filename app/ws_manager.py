import asyncio
from fastapi import WebSocket
from typing import Dict
from sqlalchemy import select, and_, or_
from app.database import async_session_maker
from app.security import encrypt_message, decrypt_message
from app.models import Friendship, OfflineMessage

async def get_user_friends(username: str) -> list:
    async with async_session_maker() as session:
        result = await session.execute(
            select(Friendship).where(
                and_(
                    or_(Friendship.requester == username, Friendship.addressee == username),
                    Friendship.status == 'accepted'
                )
            )
        )
        friendships = result.scalars().all()
        friends = []
        for f in friendships:
            if f.requester == username:
                friends.append(f.addressee)
            else:
                friends.append(f.requester)
        return friends

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        
        
        # Выгрузка офлайн сообщений
        async with async_session_maker() as session:
            result = await session.execute(
                select(OfflineMessage).where(OfflineMessage.receiver == username)
            )
            rows = result.scalars().all()
            for row in rows:
                try:
                    text = decrypt_message(row.ciphertext)
                except Exception:
                    text = "[не удалось расшифровать сообщение]"
                    
                await websocket.send_json({"action": "message", "from": row.sender, "text": text, "cid": row.cid or f"offline_{row.id}"})
                await session.delete(row)
            if rows:
                await session.commit()

    async def disconnect(self, username: str):
        self.active_connections.pop(username, None)

    async def send_message(self, text: str, receiver: str, sender: str, cid: str):
        if sender in self.active_connections:
            await self.active_connections[sender].send_json({"action": "ack", "cid": cid})

        if receiver in self.active_connections:
            await self.active_connections[receiver].send_json(
                {"action": "message", "from": sender, "text": text, "cid": cid}
            )
        else:
            async with async_session_maker() as session:
                new_msg = OfflineMessage(
                    sender=sender,
                    receiver=receiver,
                    ciphertext=encrypt_message(text),
                    cid=cid
                )
                session.add(new_msg)
                await session.commit()
    
    async def forward_event(self, action: str, receiver: str, sender: str, cid: str):
        # Пересылка системных событий (например, read receipt)
        if receiver in self.active_connections:
            await self.active_connections[receiver].send_json(
                {"action": action, "from": sender, "cid": cid}
            )

    async def notify_user(self, username: str, data: dict):
        if username in self.active_connections:
            await self.active_connections[username].send_json(data)

manager = ConnectionManager()