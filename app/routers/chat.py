import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.database import db_conn
from app.security import decode_jwt
from app.ws_manager import manager

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

    cursor = db_conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        await websocket.close(code=4403, reason="User not found")
        return

    if username in manager.active_connections:
        await websocket.close(code=4409, reason="Already connected")
        return

    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_json()
            receiver = data.get("to", "").strip()
            text = data.get("text", "").strip()

            if not receiver or not text:
                continue
            if len(text) > 4096:
                await websocket.send_json({"system": "Сообщение слишком длинное (макс. 4096)"})
                continue

            cursor.execute("SELECT 1 FROM users WHERE username = ?", (receiver,))
            if not cursor.fetchone():
                await websocket.send_json({"system": f"Пользователь '{receiver}' не найден"})
                continue

            await manager.send_message(text, receiver, username)
    except WebSocketDisconnect:
        manager.disconnect(username)