import os
from datetime import datetime, timedelta, timezone
import bcrypt as _bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from typing import Optional
import hashlib
from app.config import settings

# Ключ шифрования сообщений
fernet = Fernet(settings.msg_encryption_key.encode())

def hash_password(plain: str) -> str:
    # Предварительное хеширование SHA-256 снимает лимит bcrypt в 72 байта
    sha256_hash = hashlib.sha256(plain.encode()).hexdigest().encode()
    return _bcrypt.hashpw(sha256_hash, _bcrypt.gensalt(rounds=12)).decode()

def verify_password(plain: str, hashed: str) -> bool:
    sha256_hash = hashlib.sha256(plain.encode()).hexdigest().encode()
    return _bcrypt.checkpw(sha256_hash, hashed.encode())

# Константа для защиты от Timing Attacks
DUMMY_HASH = hash_password("dummy_password_for_timing_attack_protection")

def create_jwt(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    # Добавлены стандартные claims: iat, jti
    import uuid
    payload = {
        "sub": username, 
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def decode_jwt(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None

def encrypt_message(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt_message(ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode()).decode()

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    username = decode_jwt(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен"
        )
    return username