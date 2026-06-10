"""add origin column to suppliers

Revision ID: 20260524_400000
Revises: 20260524_300000
Create Date: 2026-05-24 40:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260524_400000'
down_revision: Union[str, None] = '20260524_300000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('suppliers', sa.Column('origin', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('suppliers', 'origin')
