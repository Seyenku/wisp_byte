"""Repository for User data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.models import User, Friendship


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def create(self, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(username=username, password_hash=password_hash)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def search_users(
        self, query: str, exclude_username: str, limit: int = 20
    ) -> List[str]:
        """Search users by username pattern."""
        # Экранирование спецсимволов для безопасности ilike
        safe_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        result = await self.session.execute(
            select(User.username)
            .where(User.username.ilike(f"%{safe_query}%"))
            .where(User.username != exclude_username)
            .limit(limit)
        )
        return result.scalars().all()
