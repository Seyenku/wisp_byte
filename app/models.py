from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)

class OfflineMessage(Base):
    __tablename__ = "offline_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender: Mapped[str] = mapped_column(String, index=True)
    receiver: Mapped[str] = mapped_column(String, index=True)
    ciphertext: Mapped[str] = mapped_column(String)
    cid: Mapped[str] = mapped_column(String, nullable=True)

class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester: Mapped[str] = mapped_column(String, index=True)
    addressee: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="pending")

    __table_args__ = (
        UniqueConstraint("requester", "addressee", name="uq_friendship_requester_addressee"),
    )
