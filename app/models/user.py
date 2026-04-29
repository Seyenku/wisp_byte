"""User model."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class User:
    """User model for authentication."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
