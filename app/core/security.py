"""Security utilities for password hashing, JWT tokens, and message encryption."""

import os
from datetime import datetime, timedelta, timezone
import bcrypt as _bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from typing import Optional
import hashlib
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings


# Message encryption key
fernet = Fernet(settings.msg_encryption_key.encode())


def hash_password(plain: str) -> str:
    """Hash a password using SHA-256 pre-hashing + bcrypt."""
    # Pre-hashing with SHA-256 removes bcrypt's 72-byte limit
    sha256_hash = hashlib.sha256(plain.encode()).hexdigest().encode()
    return _bcrypt.hashpw(sha256_hash, _bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    sha256_hash = hashlib.sha256(plain.encode()).hexdigest().encode()
    return _bcrypt.checkpw(sha256_hash, hashed.encode())


# Constant for timing attack protection
DUMMY_HASH = hash_password("dummy_password_for_timing_attack_protection")


def create_jwt(username: str) -> str:
    """Create a JWT token for a user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": username, 
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_jwt(token: str) -> Optional[str]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None


def encrypt_message(text: str) -> str:
    """Encrypt a message using Fernet symmetric encryption."""
    return fernet.encrypt(text.encode()).decode()


def decrypt_message(ciphertext: str) -> str:
    """Decrypt a message using Fernet symmetric encryption."""
    return fernet.decrypt(ciphertext.encode()).decode()


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency to get the current authenticated user from JWT token."""
    username = decode_jwt(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен"
        )
    return username
