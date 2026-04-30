"""Message service."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos_friendship import FriendshipRepository


class MessageService:
    """Service for message-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.friendship_repo = FriendshipRepository(session)

    async def can_send_message(self, sender: str, receiver: str) -> bool:
        """Check if sender can send message to receiver (they must be friends)."""
        friendship = await self.friendship_repo.get_relationship(sender, receiver)
        return friendship is not None and friendship.status == "accepted"
