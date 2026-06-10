"""add tax validity dates to suppliers

Revision ID: 20260524_300000
Revises: 20260524_200000
Create Date: 2026-05-24 30:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260524_300000'
down_revision: Union[str, None] = '20260524_200000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('suppliers', sa.Column('tax_start_date', sa.Date(), nullable=True))
    op.add_column('suppliers', sa.Column('tax_end_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('suppliers', 'tax_end_date')
    op.drop_column('suppliers', 'tax_start_date')
