"""Authentication service."""

import re
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.core.security import hash_password, verify_password, create_jwt, DUMMY_HASH
from app.models import User


class AuthService:
    """Service for authentication and registration logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, username: str, password: str) -> Optional[str]:
        """
        Register a new user.
        Returns JWT token on success, raises HTTPException on failure.
        """
        from fastapi import HTTPException

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", username):
            raise HTTPException(
                status_code=400,
                detail="Имя пользователя: 3–32 символа, только латиница, цифры, '_' и '-'",
            )

        # Validate password
        if len(password) < 8:
            raise HTTPException(
                status_code=400, detail="Пароль: минимум 8 символов"
            )
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise HTTPException(
                status_code=400,
                detail="Пароль должен содержать как минимум одну букву и одну цифру",
            )

        # Check if user exists
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise HTTPException(status_code=409, detail="Пользователь уже существует")

        # Create user
        password_hash = hash_password(password)
        await self.user_repo.create(username, password_hash)

        # Create and return JWT token
        token = create_jwt(username)
        return token

    async def login(self, username: str, password: str) -> str:
        """
        Authenticate user and return JWT token.
        Raises HTTPException on failure.
        """
        from fastapi import HTTPException, status

        user = await self.user_repo.get_by_username(username)

        if not user:
            # Dummy hashing for timing attack protection
            verify_password(password, DUMMY_HASH)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_jwt(username)
        return token
