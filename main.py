from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn
import sqlite3
import os
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet

# =================================================================
# КОНФИГУРАЦИЯ БЕЗОПАСНОСТИ
# =================================================================

# JWT
JWT_SECRET_KEY_FILE = "jwt_secret.key"
MSG_ENCRYPTION_KEY_FILE = "msg_fernet.key"

def _load_or_create_key(filepath: str, generator) -> bytes:
    """Загружает ключ из файла или генерирует новый и сохраняет."""
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return f.read().strip()
    key = generator()
    with open(filepath, "wb") as f:
        f.write(key)
    os.chmod(filepath, 0o600)  # только владелец процесса
    return key

# Ключ подписи JWT (случайные 64 hex-байта)
JWT_SECRET_KEY: str = _load_or_create_key(
    JWT_SECRET_KEY_FILE,
    lambda: os.urandom(64).hex().encode()
).decode()

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Ключ Fernet для шифрования офлайн-сообщений в БД
_fernet_raw = _load_or_create_key(MSG_ENCRYPTION_KEY_FILE, Fernet.generate_key)
fernet = Fernet(_fernet_raw)

# bcrypt используется напрямую (см. hash_password / verify_password)

# =================================================================
# БАЗА ДАННЫХ (SQLite)
# =================================================================
db_conn = sqlite3.connect("chat.db", check_same_thread=False)
db_conn.execute("PRAGMA journal_mode=WAL")   # безопаснее при конкурентном доступе
db_conn.execute("PRAGMA foreign_keys=ON")

def init_db():
    cursor = db_conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username    TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    # message хранится зашифрованным (bytes → TEXT base64 через Fernet)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offline_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sender      TEXT NOT NULL,
            receiver    TEXT NOT NULL,
            ciphertext  TEXT NOT NULL
        )
    ''')
    db_conn.commit()

init_db()

# =================================================================
# УТИЛИТЫ AUTH
# =================================================================
def hash_password(plain: str) -> str:
    # bcrypt принимает максимум 72 байта; обрезаем до явного лимита
    secret = plain.encode()[:72]
    return _bcrypt.hashpw(secret, _bcrypt.gensalt(rounds=12)).decode()

def verify_password(plain: str, hashed: str) -> bool:
    secret = plain.encode()[:72]
    return _bcrypt.checkpw(secret, hashed.encode())

def create_jwt(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_jwt(token: str) -> Optional[str]:
    """Возвращает username или None при невалидном токене."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def encrypt_message(text: str) -> str:
    """Шифрует текст сообщения, возвращает строку для хранения в БД."""
    return fernet.encrypt(text.encode()).decode()

def decrypt_message(ciphertext: str) -> str:
    """Расшифровывает сообщение из БД."""
    return fernet.decrypt(ciphertext.encode()).decode()

# =================================================================
# PYDANTIC-МОДЕЛИ
# =================================================================
class RegisterRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# =================================================================
# FASTAPI APP
# =================================================================
app = FastAPI(title="Чат-Сервер")

# =================================================================
# HTTP ENDPOINTS: РЕГИСТРАЦИЯ / ЛОГИН
# =================================================================
@app.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    if len(req.username) < 3 or len(req.username) > 32:
        raise HTTPException(status_code=400, detail="Имя пользователя: 3–32 символа")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Пароль: минимум 8 символов")

    cursor = db_conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (req.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Пользователь уже существует")

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (req.username, hash_password(req.password))
    )
    db_conn.commit()

    token = create_jwt(req.username)
    return TokenResponse(access_token=token)

@app.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    cursor = db_conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (form.username,))
    row = cursor.fetchone()

    if not row or not verify_password(form.password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_jwt(form.username)
    return TokenResponse(access_token=token)

# =================================================================
# МЕНЕДЖЕР WEBSOCKET-ПОДКЛЮЧЕНИЙ
# =================================================================
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

# =================================================================
# WEBSOCKET ENDPOINT (требует JWT в query-параметре ?token=)
# =================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    username = decode_jwt(token)
    if not username:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    # Убеждаемся, что пользователь существует в БД
    cursor = db_conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if not cursor.fetchone():
        await websocket.close(code=4403, reason="User not found")
        return

    # Один активный сеанс на пользователя
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

            # Проверяем существование получателя
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (receiver,))
            if not cursor.fetchone():
                await websocket.send_json({"system": f"Пользователь '{receiver}' не найден"})
                continue

            await manager.send_message(text, receiver, username)
    except WebSocketDisconnect:
        manager.disconnect(username)

# =================================================================
# ФРОНТЕНД
# =================================================================
html = """"""

@app.get("/")
async def get():
    return HTMLResponse(html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=12251)