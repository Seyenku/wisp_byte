import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import select, or_, and_

from app.database import async_session_maker
from app.security import decode_jwt
from app.ws_manager import manager
from app.models import User, Friendship

router = APIRouter(tags=["Чат"])

@router.get("/")
async def get():
    html_path = os.path.join("templates", "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(html_content)
    except FileNotFoundError:
        return HTMLResponse("<h1>Создайте папку templates и положите туда index.html</h1>")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    username = decode_jwt(token)
    if not username:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        if not result.scalars().first():
            await websocket.close(code=4403, reason="User not found")
            return

    if username in manager.active_connections:
        # Закрываем старое соединение, чтобы разрешить новое (защита от "зависших" сессий)
        old_ws = manager.active_connections[username]
        try:
            await old_ws.close(code=4000, reason="Connected from another location")
        except:
            pass
        await manager.disconnect(username)

    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "message")
            receiver = data.get("to", "").strip()
            cid = data.get("cid", "")
            
            if action == "read":
                # Пересылаем уведомление о прочтении обратно отправителю сообщения
                await manager.forward_event("read", receiver, username, cid)
                continue

            text = data.get("text", "").strip()

            if not receiver or not text:
                continue
            if len(text) > 4096:
                await websocket.send_json({"system": "Сообщение слишком длинное (макс. 4096)"})
                continue

            async with async_session_maker() as session:
                result = await session.execute(
                    select(Friendship).where(
                        and_(
                            or_(
                                and_(Friendship.requester == username, Friendship.addressee == receiver),
                                and_(Friendship.requester == receiver, Friendship.addressee == username)
                            ),
                            Friendship.status == 'accepted'
                        )
                    )
                )
                if not result.scalars().first():
                    await websocket.send_json({"system": f"Вы не можете писать '{receiver}', так как вы не друзья."})
                    continue

            # Передаем cid в менеджер
            await manager.send_message(text, receiver, username, cid)
        
    except WebSocketDisconnect:
        await manager.disconnect(username)