"""add applies_to to retentions

Revision ID: 20260607_000000
Revises: 20260525_100000
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260607_000000'
down_revision: Union[str, None] = '20260525_100000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'retentions',
        sa.Column('applies_to', sa.String(20), nullable=False, server_default='subtotal')
    )


def downgrade() -> None:
    op.drop_column('retentions', 'applies_to')
