"""Offline message model."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text
from app.database import Base

class OfflineMessage(Base):
    """Model for storing offline messages."""

    __tablename__ = "offline_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    cid: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
