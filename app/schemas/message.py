"""Message-related Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional


class MessageRequest(BaseModel):
    """Request schema for sending a message."""
    to: str
    text: str
    cid: Optional[str] = None


class ReadReceiptRequest(BaseModel):
    """Request schema for read receipt."""
    to: str
    cid: str
