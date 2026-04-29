"""add_cid_to_offline

Revision ID: 002
Revises: 001
Create Date: 2026-04-28 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('offline_messages', sa.Column('cid', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('offline_messages', 'cid')
