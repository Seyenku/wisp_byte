from fastapi import APIRouter, Depends

from app.database import get_db_session
from app.core.security import get_current_user
from app.dependencies import get_friend_service
from app.services.friend import FriendService
from app.schemas import FriendActionRequest, UserSearchItem, FriendSuggestion
from typing import List


router = APIRouter(prefix="/friends", tags=["Друзья"])


@router.get("/search", response_model=List[UserSearchItem])
async def search_users(
    query: str,
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Search users and return their friendship status."""
    results = await friend_service.search_users(query, current_user)
    return [UserSearchItem(**r) for r in results]


@router.post("/request")
async def send_friend_request(
    req: FriendActionRequest,
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Send a friend request to a user."""
    result = await friend_service.send_friend_request(current_user, req.target_username)
    
    # WebSocket notification
    from app.core.websocket import manager
    await manager.notify_user(req.target_username, {"system": "friend_request", "from": current_user})
    
    return result


@router.post("/accept")
async def accept_friend_request(
    req: FriendActionRequest,
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Accept a friend request."""
    result = await friend_service.accept_friend_request(current_user, req.target_username)
    
    # WebSocket notification
    from app.core.websocket import manager
    await manager.notify_user(req.target_username, {"system": "request_accepted", "from": current_user})
    
    return result


@router.post("/reject")
async def reject_friend_request(
    req: FriendActionRequest,
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Reject a friend request."""
    return await friend_service.reject_friend_request(current_user, req.target_username)


@router.post("/cancel")
async def cancel_friend_request(
    req: FriendActionRequest,
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Cancel a sent friend request."""
    return await friend_service.cancel_friend_request(current_user, req.target_username)


@router.post("/remove")
async def remove_friend(
    req: FriendActionRequest,
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Remove a user from friends."""
    result = await friend_service.remove_friend(current_user, req.target_username)
    
    # WebSocket notification
    from app.core.websocket import manager
    await manager.notify_user(req.target_username, {"system": "friend_removed", "from": current_user})
    
    return result


@router.get("/requests", response_model=List[str])
async def get_incoming_requests(
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Get list of incoming friend requests."""
    return await friend_service.get_incoming_requests(current_user)


@router.get("/list")
async def get_friends_list(
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Get list of friends with online status."""
    return await friend_service.get_friends_list(current_user)


@router.get("/suggestions", response_model=List[FriendSuggestion])
async def get_friend_suggestions(
    current_user: str = Depends(get_current_user),
    friend_service: FriendService = Depends(get_friend_service),
):
    """Get friend suggestions based on mutual friends."""
    suggestions = await friend_service.get_friend_suggestions(current_user)
    return [FriendSuggestion(**s) for s in suggestions]