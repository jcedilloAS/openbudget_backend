"""add tax withholding fields to requisitions

Revision ID: 20260524_200000
Revises: 20260524_100000
Create Date: 2026-05-24 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260524_200000'
down_revision: Union[str, None] = '20260524_100000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('requisitions', sa.Column('isr_withheld_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'))
    op.add_column('requisitions', sa.Column('iva_withheld_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'))
    op.add_column('requisitions', sa.Column('net_amount', sa.Numeric(15, 2), nullable=False, server_default='0.00'))


def downgrade() -> None:
    op.drop_column('requisitions', 'net_amount')
    op.drop_column('requisitions', 'iva_withheld_amount')
    op.drop_column('requisitions', 'isr_withheld_amount')
