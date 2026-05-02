import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import async_session_maker
from app.core.security import decode_jwt
from app.core.websocket import manager
from app.services.service_message import MessageService
from app.dependencies import get_message_service
from app.models import User


# Setup templates locally to avoid circular import
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


router = APIRouter(tags=["Чат"])


@router.get("/")
async def get(request: Request):
    """Serve the main chat page."""
    # Get user from JWT token in cookies or headers
    token = request.cookies.get("access_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    username = decode_jwt(token) if token else None
    
    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "username": username or "Гость",
            "user_id": 0  # Will be populated by frontend after login
        }
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    """WebSocket endpoint for real-time chat."""
    username = decode_jwt(token)
    if not username:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == username))
        if not result.scalars().first():
            await websocket.close(code=4403, reason="User not found")
            return

    if username in manager.active_connections:
        # Close old connection to allow new one
        old_ws = manager.active_connections[username]
        try:
            await old_ws.close(code=4000, reason="Connected from another location")
        except Exception:
            pass
        await manager.disconnect(username)

    # Pass token for additional validation in connect method
    await manager.connect(websocket, username, token)
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "message")
            receiver = data.get("to", "").strip()
            cid = data.get("cid", "")
            
            if action == "read":
                # Forward read receipt to sender
                await manager.forward_event("read", receiver, username, cid)
                continue

            text = data.get("text", "").strip()

            if not receiver or not text:
                continue
            if len(text) > 4096:
                await websocket.send_json({"system": "Сообщение слишком длинное (макс. 4096)"})
                continue

            # Check if users are friends using service layer
            async with async_session_maker() as session:
                message_service = MessageService(session)
                if not await message_service.can_send_message(username, receiver):
                    await websocket.send_json({
                        "system": f"Вы не можете писать '{receiver}', так как вы не друзья."
                    })
                    continue

            # Send message via manager
            await manager.send_message(text, receiver, username, cid)
        
    except WebSocketDisconnect:
        await manager.disconnect(username)
    except Exception as e:
        # Handle all other exceptions gracefully
        try:
            await websocket.send_json({"system": f"Ошибка: {str(e)}"})
        except Exception:
            pass
        await manager.disconnect(username)