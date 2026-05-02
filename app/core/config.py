"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    # Application Settings
    app_env: str = "production"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/wispchat.db"
    
    # Security keys - MUST be set in .env for production!
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str
    encryption_key: str  # Must be 32 bytes (64 hex chars) for AES-256
    
    # JWT Settings
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_ws_connections_per_ip: int = 10
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    def validate_keys(self):
        """Validate that security keys are properly configured."""
        if self.secret_key == "your-secret-key-here-change-in-production":
            raise ValueError(
                "SECRET_KEY is not configured! "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\" "
                "and add it to your .env file"
            )
        
        if self.encryption_key == "your-encryption-key-here-32-bytes-hex":
            raise ValueError(
                "ENCRYPTION_KEY is not configured! "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\" "
                "and add it to your .env file"
            )
        
        # Validate encryption key length (must be 32 bytes = 64 hex characters)
        try:
            key_bytes = bytes.fromhex(self.encryption_key)
            if len(key_bytes) != 32:
                raise ValueError(
                    f"ENCRYPTION_KEY must be 32 bytes (64 hex characters), got {len(key_bytes)} bytes"
                )
        except ValueError as e:
            if "must be 32 bytes" in str(e):
                raise
            raise ValueError(
                "ENCRYPTION_KEY must be a valid hex string. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )


settings = Settings()
settings.validate_keys()
