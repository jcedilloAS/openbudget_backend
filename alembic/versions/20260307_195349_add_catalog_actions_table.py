"""add catalog_actions table with default relationships

Revision ID: 20260307_195349
Revises: 20260307_194447
Create Date: 2026-03-07 19:53:49.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260307_195349'
down_revision: Union[str, None] = '20260307_194447'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create catalog_actions table
    op.create_table('catalog_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('catalog_id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['catalog_id'], ['catalogs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_id'], ['actions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('catalog_id', 'action_id', name='uq_catalog_action')
    )
    op.create_index(op.f('ix_catalog_actions_id'), 'catalog_actions', ['id'], unique=False)
    
    # Insert default relationships: all catalogs with create, read, update, delete actions
    # Using raw SQL with subqueries to get the IDs dynamically
    op.execute("""
        INSERT INTO catalog_actions (catalog_id, action_id, is_active)
        SELECT c.id, a.id, true
        FROM catalogs c
        CROSS JOIN actions a
        WHERE a.action_code IN ('create', 'update', 'delete', 'list')
        AND c.is_active = true
        AND a.is_active = true
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_catalog_actions_id'), table_name='catalog_actions')
    op.drop_table('catalog_actions')
