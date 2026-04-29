from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class FriendActionRequest(BaseModel):
    target_username: str

class UserSearchItem(BaseModel):
    username: str
    status: str # 'none', 'pending_sent', 'pending_received', 'friends'