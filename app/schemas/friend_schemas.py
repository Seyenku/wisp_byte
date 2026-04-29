"""Friend-related Pydantic schemas."""

from pydantic import BaseModel
from typing import List


class FriendActionRequest(BaseModel):
    """Request schema for friend actions (add, remove, accept, reject)."""
    target_username: str


class UserSearchItem(BaseModel):
    """Schema for user search results."""
    username: str
    status: str  # 'none', 'pending_sent', 'pending_received', 'friends'


class FriendSuggestion(BaseModel):
    """Schema for friend suggestions."""
    username: str
    mutual_count: int
