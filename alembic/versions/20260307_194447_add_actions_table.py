"""add actions table with seed data

Revision ID: 20260307_194447
Revises: 20260307_192225
Create Date: 2026-03-07 19:44:47.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '20260307_194447'
down_revision: Union[str, None] = '20260307_192225'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create actions table
    op.create_table('actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action_code', sa.String(length=50), nullable=False),
        sa.Column('action_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_actions_action_code'), 'actions', ['action_code'], unique=True)
    op.create_index(op.f('ix_actions_id'), 'actions', ['id'], unique=False)
    
    # Insert seed data (fixed action values)
    actions_table = table('actions',
        column('action_code', sa.String),
        column('action_name', sa.String),
        column('description', sa.String),
        column('is_active', sa.Boolean),
    )
    
    op.bulk_insert(actions_table, [
        {
            'action_code': 'create',
            'action_name': 'Crear',
            'description': 'Permiso para crear nuevos registros',
            'is_active': True
        },
        {
            'action_code': 'read',
            'action_name': 'Leer',
            'description': 'Permiso para leer/visualizar registros',
            'is_active': True
        },
        {
            'action_code': 'update',
            'action_name': 'Actualizar',
            'description': 'Permiso para actualizar registros existentes',
            'is_active': True
        },
        {
            'action_code': 'delete',
            'action_name': 'Eliminar',
            'description': 'Permiso para eliminar registros',
            'is_active': True
        },
        {
            'action_code': 'list',
            'action_name': 'Listar',
            'description': 'Permiso para listar registros',
            'is_active': True
        },
        {
            'action_code': 'search',
            'action_name': 'Buscar',
            'description': 'Permiso para buscar registros',
            'is_active': True
        },
        {
            'action_code': 'export',
            'action_name': 'Exportar',
            'description': 'Permiso para exportar datos',
            'is_active': True
        },
        {
            'action_code': 'import',
            'action_name': 'Importar',
            'description': 'Permiso para importar datos',
            'is_active': True
        },
        {
            'action_code': 'approve',
            'action_name': 'Aprobar',
            'description': 'Permiso para aprobar registros',
            'is_active': True
        },
        {
            'action_code': 'reject',
            'action_name': 'Rechazar',
            'description': 'Permiso para rechazar registros',
            'is_active': True
        },
        {
            'action_code': 'view_details',
            'action_name': 'Ver Detalles',
            'description': 'Permiso para ver detalles completos de registros',
            'is_active': True
        },
        {
            'action_code': 'download',
            'action_name': 'Descargar',
            'description': 'Permiso para descargar archivos o documentos',
            'is_active': True
        },
        {
            'action_code': 'upload',
            'action_name': 'Subir',
            'description': 'Permiso para subir archivos o documentos',
            'is_active': True
        },
        {
            'action_code': 'print',
            'action_name': 'Imprimir',
            'description': 'Permiso para imprimir documentos',
            'is_active': True
        }
    ])


def downgrade() -> None:
    op.drop_index(op.f('ix_actions_id'), table_name='actions')
    op.drop_index(op.f('ix_actions_action_code'), table_name='actions')
    op.drop_table('actions')
