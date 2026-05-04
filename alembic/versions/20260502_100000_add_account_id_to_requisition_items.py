"""add_account_id_to_requisition_items

Revision ID: 20260502_100000
Revises: e5775aad339f
Create Date: 2026-05-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260502_100000'
down_revision: Union[str, None] = 'e5775aad339f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'requisition_items',
        sa.Column('account_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_requisition_items_account_id',
        'requisition_items', 'accounts',
        ['account_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(
        'ix_requisition_items_account_id',
        'requisition_items', ['account_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_requisition_items_account_id', table_name='requisition_items')
    op.drop_constraint('fk_requisition_items_account_id', 'requisition_items', type_='foreignkey')
    op.drop_column('requisition_items', 'account_id')
