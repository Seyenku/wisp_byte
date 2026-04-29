"""User service."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository


class UserService:
    """Service for user-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_user_by_username(self, username: str) -> Optional[str]:
        """Get user by username. Returns username if exists, None otherwise."""
        user = await self.user_repo.get_by_username(username)
        return user.username if user else None

    async def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        user = await self.user_repo.get_by_username(username)
        return user is not None
