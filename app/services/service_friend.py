"""Friend service."""

from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos_user import UserRepository
from app.repositories.repos_friendship import FriendshipRepository
from app.models import User


class FriendService:
    """Service for friend-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.friendship_repo = FriendshipRepository(session)

    async def search_users(
        self, query: str, current_user: str
    ) -> List[Dict[str, str]]:
        """Search users and return their friendship status with current user."""
        if len(query) < 3:
            return []

        # Get matching usernames
        usernames = await self.user_repo.search_users(query, current_user)
        if not usernames:
            return []

        # Get relationships for all found users in one query
        rel_map = await self.friendship_repo.get_relationships_for_users(
            current_user, usernames
        )

        results = []
        for username in usernames:
            rel = rel_map.get(username)
            status = "none"
            if rel:
                if rel.status == "accepted":
                    status = "friends"
                elif rel.requester == current_user:
                    status = "pending_sent"
                else:
                    status = "pending_received"

            results.append({"username": username, "status": status})

        return results

    async def send_friend_request(
        self, requester: str, target_username: str
    ) -> Dict[str, str]:
        """Send a friend request."""
        from fastapi import HTTPException

        if target_username == requester:
            raise HTTPException(status_code=400, detail="Нельзя добавить самого себя")

        # Check if target user exists
        target_user = await self.user_repo.get_by_username(target_username)
        if not target_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Check if relationship already exists
        existing_rel = await self.friendship_repo.get_relationship(
            requester, target_username
        )
        if existing_rel:
            raise HTTPException(
                status_code=400, detail="Заявка уже существует или вы уже друзья"
            )

        # Create new request
        await self.friendship_repo.create_request(requester, target_username)

        return {"message": "Заявка отправлена"}

    async def accept_friend_request(
        self, current_user: str, target_username: str
    ) -> Dict[str, str]:
        """Accept a friend request."""
        from fastapi import HTTPException

        friendship = await self.friendship_repo.get_pending_request(
            target_username, current_user
        )
        if not friendship:
            raise HTTPException(status_code=404, detail="Активная заявка не найдена")

        await self.friendship_repo.accept_request(friendship)

        return {"message": "Заявка принята"}

    async def reject_friend_request(
        self, current_user: str, target_username: str
    ) -> Dict[str, str]:
        """Reject a friend request."""
        from fastapi import HTTPException

        friendship = await self.friendship_repo.get_pending_request(
            target_username, current_user
        )
        if not friendship:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

        await self.friendship_repo.delete_friendship(friendship)

        return {"message": "Заявка отклонена"}

    async def cancel_friend_request(
        self, current_user: str, target_username: str
    ) -> Dict[str, str]:
        """Cancel a sent friend request."""
        from fastapi import HTTPException

        friendship = await self.friendship_repo.get_pending_request(
            current_user, target_username
        )
        if not friendship:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

        await self.friendship_repo.delete_friendship(friendship)

        return {"message": "Заявка отозвана"}

    async def remove_friend(
        self, current_user: str, target_username: str
    ) -> Dict[str, str]:
        """Remove a friend."""
        from fastapi import HTTPException

        friendship = await self.friendship_repo.get_relationship(
            current_user, target_username
        )
        if not friendship or friendship.status != "accepted":
            raise HTTPException(status_code=404, detail="Друг не найден")

        await self.friendship_repo.delete_friendship(friendship)

        return {"message": "Пользователь удален из друзей"}

    async def get_incoming_requests(self, username: str) -> List[str]:
        """Get list of incoming friend requests."""
        return await self.friendship_repo.get_incoming_requests(username)

    async def get_friends_list(self, username: str) -> List[Dict[str, Any]]:
        """Get list of friends with online status."""
        from app.core.websocket import manager

        friends = await self.friendship_repo.get_friends_list(username)
        return [
            {"username": f, "online": f in manager.active_connections}
            for f in friends
        ]

    async def get_friend_suggestions(
        self, current_user: str
    ) -> List[Dict[str, Any]]:
        """Get friend suggestions based on mutual friends."""
        # Get all relationships and friends
        related_users, my_friends = await self.friendship_repo.get_all_relationships(
            current_user
        )

        if not my_friends:
            return []

        # Find friends of friends
        suggestions = await self.friendship_repo.get_friends_of_friends(
            my_friends, related_users
        )

        return [{"username": name, "mutual_count": cnt} for name, cnt in suggestions]
