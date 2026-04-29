"""Core module containing configuration, security, and other shared utilities."""

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_jwt,
    decode_jwt,
    encrypt_message,
    decrypt_message,
    get_current_user,
    DUMMY_HASH,
)

__all__ = [
    "settings",
    "hash_password",
    "verify_password",
    "create_jwt",
    "decode_jwt",
    "encrypt_message",
    "decrypt_message",
    "get_current_user",
    "DUMMY_HASH",
]
