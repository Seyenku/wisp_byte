"""Pydantic schemas for request/response validation."""

from app.schemas.auth_schemas import RegisterRequest, TokenResponse
from app.schemas.friend_schemas import FriendActionRequest, UserSearchItem, FriendSuggestion

__all__ = [
    "RegisterRequest",
    "TokenResponse", 
    "FriendActionRequest",
    "UserSearchItem",
    "FriendSuggestion",
]
