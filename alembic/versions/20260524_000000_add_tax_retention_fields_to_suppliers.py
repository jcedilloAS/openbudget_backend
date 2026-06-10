"""add tax retention fields to suppliers

Revision ID: 20260524_000000
Revises: 20260502_100000
Create Date: 2026-05-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260524_000000'
down_revision: Union[str, None] = '20260502_100000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('suppliers', sa.Column('isr_withheld_professional_fees', sa.Numeric(5, 2), nullable=True))
    op.add_column('suppliers', sa.Column('isr_withheld_resico', sa.Numeric(5, 2), nullable=True))
    op.add_column('suppliers', sa.Column('iva_withheld_professional_fees', sa.Numeric(5, 2), nullable=True))
    op.add_column('suppliers', sa.Column('iva_withheld_resico', sa.Numeric(5, 2), nullable=True))
    op.add_column('suppliers', sa.Column('iva_withheld_freight', sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('suppliers', 'iva_withheld_freight')
    op.drop_column('suppliers', 'iva_withheld_resico')
    op.drop_column('suppliers', 'iva_withheld_professional_fees')
    op.drop_column('suppliers', 'isr_withheld_resico')
    op.drop_column('suppliers', 'isr_withheld_professional_fees')
