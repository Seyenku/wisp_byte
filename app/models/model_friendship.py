"""Friendship model."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint
from app.database import Base

class Friendship(Base):
    """Model for friendship relationships."""

    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    addressee: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    __table_args__ = (
        UniqueConstraint("requester", "addressee", name="uq_friendship_requester_addressee"),
    )
