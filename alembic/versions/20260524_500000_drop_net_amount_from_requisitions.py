"""drop net_amount from requisitions

Revision ID: 20260524_500000
Revises: 20260524_200000
Create Date: 2026-05-24 50:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260524_500000'
down_revision: Union[str, None] = '20260524_400000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('requisitions', 'net_amount')


def downgrade() -> None:
    op.add_column('requisitions', sa.Column('net_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'))
