"""Offline message model."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.database import Base

class OfflineMessage:
    """Model for storing offline messages."""

    __tablename__ = "offline_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender: Mapped[str] = mapped_column(String, index=True)
    receiver: Mapped[str] = mapped_column(String, index=True)
    ciphertext: Mapped[str] = mapped_column(String)
    cid: Mapped[str] = mapped_column(String, nullable=True)
