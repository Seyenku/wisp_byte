import os
from datetime import datetime, timedelta, timezone
import bcrypt as _bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from typing import Optional

JWT_SECRET_KEY_FILE = "jwt_secret.key"
MSG_ENCRYPTION_KEY_FILE = "msg_fernet.key"

def _load_or_create_key(filepath: str, generator) -> bytes:
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return f.read().strip()
    key = generator()
    with open(filepath, "wb") as f:
        f.write(key)
    os.chmod(filepath, 0o600)  # Доступ только процессу-владельцу
    return key

# Ключ подписи JWT
JWT_SECRET_KEY: str = _load_or_create_key(
    JWT_SECRET_KEY_FILE,
    lambda: os.urandom(64).hex().encode()
).decode()

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Ключ шифрования сообщений
_fernet_raw = _load_or_create_key(MSG_ENCRYPTION_KEY_FILE, Fernet.generate_key)
fernet = Fernet(_fernet_raw)

def hash_password(plain: str) -> str:
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
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def encrypt_message(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt_message(ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode()).decode()