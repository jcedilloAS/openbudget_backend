"""add catalogs table with seed data

Revision ID: 20260307_192225
Revises: fa1e487451f0
Create Date: 2026-03-07 19:22:25.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '20260307_192225'
down_revision: Union[str, None] = 'fa1e487451f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create catalogs table
    op.create_table('catalogs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('catalog_code', sa.String(length=50), nullable=False),
        sa.Column('catalog_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_catalogs_catalog_code'), 'catalogs', ['catalog_code'], unique=True)
    op.create_index(op.f('ix_catalogs_id'), 'catalogs', ['id'], unique=False)
    
    # Insert seed data (fixed catalog values)
    catalogs_table = table('catalogs',
        column('catalog_code', sa.String),
        column('catalog_name', sa.String),
        column('description', sa.String),
        column('is_active', sa.Boolean),
    )
    
    op.bulk_insert(catalogs_table, [
        {
            'catalog_code': 'users',
            'catalog_name': 'Usuarios',
            'description': 'Catálogo de usuarios del sistema',
            'is_active': True
        },
        {
            'catalog_code': 'projects',
            'catalog_name': 'Proyectos',
            'description': 'Catálogo de proyectos',
            'is_active': True
        },
        {
            'catalog_code': 'audit',
            'catalog_name': 'Bitácora',
            'description': 'Catálogo de bitácora de eventos',
            'is_active': True
        },
        {
            'catalog_code': 'accounts',
            'catalog_name': 'Cuentas',
            'description': 'Catálogo de cuentas contables',
            'is_active': True
        },
        {
            'catalog_code': 'retentions',
            'catalog_name': 'Retenciones',
            'description': 'Catálogo de retenciones fiscales',
            'is_active': True
        },
        {
            'catalog_code': 'suppliers',
            'catalog_name': 'Proveedores',
            'description': 'Catálogo de proveedores',
            'is_active': True
        },
        {
            'catalog_code': 'requisitions',
            'catalog_name': 'Requisiciones',
            'description': 'Catálogo de requisiciones',
            'is_active': True
        },
        {
            'catalog_code': 'roles',
            'catalog_name': 'Roles',
            'description': 'Catálogo de roles',
            'is_active': True
        }
    ])


def downgrade() -> None:
    op.drop_index(op.f('ix_catalogs_id'), table_name='catalogs')
    op.drop_index(op.f('ix_catalogs_catalog_code'), table_name='catalogs')
    op.drop_table('catalogs')
