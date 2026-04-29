"""WebSocket connection manager."""

import asyncio
from typing import Dict

from fastapi import WebSocket

from app.database import async_session_maker
from app.core.security import encrypt_message, decrypt_message
from app.models import Friendship, OfflineMessage, User


async def get_user_friends(username: str) -> list:
    """Get list of friends for a user."""
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
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        """Accept WebSocket connection and store it."""
        await websocket.accept()
        self.active_connections[username] = websocket
        
        # Notify friends that user is online
        await self.notify_friends_status(username, True)

        # Load offline messages
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
                    
                await websocket.send_json({
                    "action": "message",
                    "from": row.sender,
                    "text": text,
                    "cid": row.cid or f"offline_{row.id}"
                })
                await session.delete(row)
            if rows:
                await session.commit()

    async def disconnect(self, username: str):
        """Remove WebSocket connection and notify friends."""
        self.active_connections.pop(username, None)
        # Notify friends that user is offline
        await self.notify_friends_status(username, False)

    async def send_message(self, text: str, receiver: str, sender: str, cid: str):
        """Send message to receiver or store as offline."""
        if sender in self.active_connections:
            await self.active_connections[sender].send_json({
                "action": "ack",
                "cid": cid
            })

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
        """Forward system events (e.g., read receipts)."""
        if receiver in self.active_connections:
            await self.active_connections[receiver].send_json(
                {"action": action, "from": sender, "cid": cid}
            )

    async def notify_user(self, username: str, data: dict):
        """Send notification to a specific user."""
        if username in self.active_connections:
            await self.active_connections[username].send_json(data)

    async def notify_friends_status(self, username: str, online: bool):
        """Notify all friends about user's online status change."""
        friends = await get_user_friends(username)
        for friend in friends:
            if friend in self.active_connections:
                await self.active_connections[friend].send_json({
                    "action": "user_status",
                    "user": username,
                    "online": online
                })


manager = ConnectionManager()

# Import here to avoid circular imports
from sqlalchemy import select, and_, or_
