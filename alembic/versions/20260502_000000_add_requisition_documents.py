"""add_requisition_documents

Revision ID: 20260502_000000
Revises: b7e2a4f91d3c
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260502_000000'
down_revision: Union[str, None] = 'b7e2a4f91d3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'requisition_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('requisition_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('document_url', sa.String(length=1000), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['requisition_id'], ['requisitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_requisition_documents_id'), 'requisition_documents', ['id'], unique=False)
    op.create_index(op.f('ix_requisition_documents_requisition_id'), 'requisition_documents', ['requisition_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_requisition_documents_requisition_id'), table_name='requisition_documents')
    op.drop_index(op.f('ix_requisition_documents_id'), table_name='requisition_documents')
    op.drop_table('requisition_documents')
