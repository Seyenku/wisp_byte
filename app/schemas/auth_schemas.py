"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
