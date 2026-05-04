"""add_must_change_password

Revision ID: b7e2a4f91d3c
Revises: a3f8d1c29e74
Create Date: 2026-05-01 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2a4f91d3c'
down_revision: Union[str, None] = 'a3f8d1c29e74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('must_change_password', sa.Boolean(), nullable=True, server_default=sa.false())
    )


def downgrade() -> None:
    op.drop_column('users', 'must_change_password')
