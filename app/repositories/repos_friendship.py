"""Repository for Friendship data access."""

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Set, Tuple

from app.models import Friendship


class FriendshipRepository:
    """Repository for friendship-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_relationship(
        self, user1: str, user2: str
    ) -> Optional[Friendship]:
        """Get friendship relationship between two users (any direction)."""
        result = await self.session.execute(
            select(Friendship).where(
                or_(
                    and_(
                        Friendship.requester == user1, Friendship.addressee == user2
                    ),
                    and_(
                        Friendship.requester == user2, Friendship.addressee == user1
                    ),
                )
            )
        )
        return result.scalars().first()

    async def get_pending_request(
        self, requester: str, addressee: str
    ) -> Optional[Friendship]:
        """Get pending friendship request from requester to addressee."""
        result = await self.session.execute(
            select(Friendship).where(
                and_(
                    Friendship.requester == requester,
                    Friendship.addressee == addressee,
                    Friendship.status == "pending",
                )
            )
        )
        return result.scalars().first()

    async def create_request(self, requester: str, addressee: str) -> Friendship:
        """Create a new pending friendship request."""
        friendship = Friendship(
            requester=requester, addressee=addressee, status="pending"
        )
        self.session.add(friendship)
        await self.session.commit()
        await self.session.refresh(friendship)
        return friendship

    async def accept_request(self, friendship: Friendship) -> None:
        """Accept a friendship request."""
        friendship.status = "accepted"
        await self.session.commit()

    async def delete_friendship(self, friendship: Friendship) -> None:
        """Delete a friendship or request."""
        await self.session.delete(friendship)
        await self.session.commit()

    async def get_incoming_requests(self, username: str) -> List[str]:
        """Get list of usernames with incoming pending requests."""
        result = await self.session.execute(
            select(Friendship.requester).where(
                and_(
                    Friendship.addressee == username, Friendship.status == "pending"
                )
            )
        )
        return result.scalars().all()

    async def get_friends_list(self, username: str) -> List[str]:
        """Get list of accepted friends."""
        result = await self.session.execute(
            select(Friendship).where(
                and_(
                    or_(
                        Friendship.requester == username,
                        Friendship.addressee == username,
                    ),
                    Friendship.status == "accepted",
                )
            )
        )
        friendships = result.scalars().all()
        friends = []
        for f in friendships:
            if f.requester == username:
                friends.append(f.addressee)
            else:
                friends.append(f.requester)
        return friends

    async def get_all_relationships(
        self, username: str
    ) -> Tuple[Set[str], Set[str]]:
        """
        Get all related users and accepted friends.
        Returns: (related_users, my_friends)
        """
        result = await self.session.execute(
            select(Friendship).where(
                or_(
                    Friendship.requester == username,
                    Friendship.addressee == username,
                )
            )
        )
        related_users = {username}
        my_friends = set()

        for f in result.scalars().all():
            other = (
                f.addressee if f.requester == username else f.requester
            )
            related_users.add(other)
            if f.status == "accepted":
                my_friends.add(other)

        return related_users, my_friends

    async def get_friends_of_friends(
        self, friend_usernames: Set[str], excluded_users: Set[str]
    ) -> List[Tuple[str, int]]:
        """
        Find friends of friends (second degree connections).
        Returns list of (candidate_username, mutual_friend_count) sorted by count.
        """
        if not friend_usernames:
            return []

        result = await self.session.execute(
            select(Friendship).where(
                and_(
                    or_(
                        Friendship.requester.in_(friend_usernames),
                        Friendship.addressee.in_(friend_usernames),
                    ),
                    Friendship.status == "accepted",
                    ~Friendship.requester.in_(excluded_users),
                    ~Friendship.addressee.in_(excluded_users),
                )
            )
        )

        potential_friendships = result.scalars().all()
        counts = {}

        for f in potential_friendships:
            p1, p2 = f.requester, f.addressee
            # Один из участников — наш друг, второй — кандидат
            candidate = p1 if p1 not in friend_usernames else p2

            if candidate not in excluded_users:
                counts[candidate] = counts.get(candidate, 0) + 1

        sorted_suggestions = sorted(counts.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]
        return sorted_suggestions

    async def get_relationships_for_users(
        self, current_user: str, target_usernames: List[str]
    ) -> dict:
        """
        Get all relationships between current user and a list of target users.
        Returns dict: {target_username: Friendship}
        """
        if not target_usernames:
            return {}

        result = await self.session.execute(
            select(Friendship).where(
                or_(
                    and_(
                        Friendship.requester == current_user,
                        Friendship.addressee.in_(target_usernames),
                    ),
                    and_(
                        Friendship.addressee == current_user,
                        Friendship.requester.in_(target_usernames),
                    ),
                )
            )
        )

        rel_map = {}
        for f in result.scalars().all():
            other = (
                f.addressee if f.requester == current_user else f.requester
            )
            rel_map[other] = f

        return rel_map
