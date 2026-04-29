from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import secrets
from cryptography.fernet import Fernet

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./chat.db"
    port: int = 12251
    host: str = "0.0.0.0"
    
    # Ключи безопасности - если не заданы в .env, генерируются случайно для dev-режима
    secret_key: str = secrets.token_hex(32)
    msg_encryption_key: str = Fernet.generate_key().decode() 
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15 # Уменьшено до 15 минут для безопасности
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
