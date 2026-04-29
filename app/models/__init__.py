from sqlalchemy.orm import registry

# Create the registry first
mapper_registry = registry()

# Import model classes and bind them to the registry at definition time
# We use a helper to create classes bound to our registry
def create_model_class(classname, tablename, columns, table_args=None):
    """Helper to create SQLAlchemy model classes bound to our registry."""
    attrs = {
        '__tablename__': tablename,
        **columns
    }
    if table_args:
        attrs['__table_args__'] = table_args
    return mapper_registry.mapped(type(classname, (object,), attrs))


# Define column helpers
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint

# Create User model
User = create_model_class(
    'User',
    'users',
    {
        'username': mapped_column(String(32), primary_key=True, index=True),
        'password_hash': mapped_column(String),
    }
)

# Create OfflineMessage model
OfflineMessage = create_model_class(
    'OfflineMessage',
    'offline_messages',
    {
        'id': mapped_column(Integer, primary_key=True, autoincrement=True),
        'sender': mapped_column(String, index=True),
        'receiver': mapped_column(String, index=True),
        'ciphertext': mapped_column(String),
        'cid': mapped_column(String, nullable=True),
    }
)

# Create Friendship model
Friendship = create_model_class(
    'Friendship',
    'friendships',
    {
        'id': mapped_column(Integer, primary_key=True, autoincrement=True),
        'requester': mapped_column(String, index=True),
        'addressee': mapped_column(String, index=True),
        'status': mapped_column(String, default="pending"),
    },
    (UniqueConstraint("requester", "addressee", name="uq_friendship_requester_addressee"),)
)

# Generate the Base class for backward compatibility
Base = mapper_registry.generate_base()

__all__ = ["User", "OfflineMessage", "Friendship", "Base"]
