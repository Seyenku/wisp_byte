"""User model."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.database import Base

class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(32), primary_key=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
