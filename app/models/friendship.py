"""Friendship model."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint


class Friendship:
    """Model for friendship relationships."""

    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester: Mapped[str] = mapped_column(String, index=True)
    addressee: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="pending")

    __table_args__ = (
        UniqueConstraint("requester", "addressee", name="uq_friendship_requester_addressee"),
    )
