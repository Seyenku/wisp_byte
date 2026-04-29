"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.core.security import get_current_user
from app.services.auth import AuthService
from app.services.friend import FriendService
from app.services.message import MessageService
from app.services.user import UserService


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(session)


def get_friend_service(session: AsyncSession = Depends(get_db_session)) -> FriendService:
    """Dependency to get FriendService instance."""
    return FriendService(session)


def get_message_service(session: AsyncSession = Depends(get_db_session)) -> MessageService:
    """Dependency to get MessageService instance."""
    return MessageService(session)


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    """Dependency to get UserService instance."""
    return UserService(session)


__all__ = [
    "get_db_session",
    "get_current_user",
    "get_auth_service",
    "get_friend_service",
    "get_message_service",
    "get_user_service",
]
