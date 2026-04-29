"""initial

Revision ID: 001
Revises: 
Create Date: 2026-04-28 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('username')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    
    op.create_table('offline_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sender', sa.String(), nullable=False),
        sa.Column('receiver', sa.String(), nullable=False),
        sa.Column('ciphertext', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offline_messages_receiver'), 'offline_messages', ['receiver'], unique=False)
    op.create_index(op.f('ix_offline_messages_sender'), 'offline_messages', ['sender'], unique=False)
    
    op.create_table('friendships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('requester', sa.String(), nullable=False),
        sa.Column('addressee', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('requester', 'addressee', name='uq_friendship_requester_addressee')
    )
    op.create_index(op.f('ix_friendships_addressee'), 'friendships', ['addressee'], unique=False)
    op.create_index(op.f('ix_friendships_requester'), 'friendships', ['requester'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_friendships_requester'), table_name='friendships')
    op.drop_index(op.f('ix_friendships_addressee'), table_name='friendships')
    op.drop_table('friendships')
    
    op.drop_index(op.f('ix_offline_messages_sender'), table_name='offline_messages')
    op.drop_index(op.f('ix_offline_messages_receiver'), table_name='offline_messages')
    op.drop_table('offline_messages')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
