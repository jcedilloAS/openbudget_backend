"""add cascade deletes to foreign keys

Revision ID: 20260403_130000
Revises: 20260403_120000
Create Date: 2026-04-03 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260403_130000'
down_revision: Union[str, None] = '20260403_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_projects.user_id -> CASCADE
    op.drop_constraint('user_projects_user_id_fkey', 'user_projects', type_='foreignkey')
    op.create_foreign_key('user_projects_user_id_fkey', 'user_projects', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # user_projects.project_id -> CASCADE
    op.drop_constraint('user_projects_project_id_fkey', 'user_projects', type_='foreignkey')
    op.create_foreign_key('user_projects_project_id_fkey', 'user_projects', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

    # supplier_documents.supplier_id -> CASCADE
    op.drop_constraint('supplier_documents_supplier_id_fkey', 'supplier_documents', type_='foreignkey')
    op.create_foreign_key('supplier_documents_supplier_id_fkey', 'supplier_documents', 'suppliers', ['supplier_id'], ['id'], ondelete='CASCADE')

    # requisitions.supplier_id -> SET NULL
    op.drop_constraint('requisitions_supplier_id_fkey', 'requisitions', type_='foreignkey')
    op.create_foreign_key('requisitions_supplier_id_fkey', 'requisitions', 'suppliers', ['supplier_id'], ['id'], ondelete='SET NULL')

    # requisitions.retention_id -> SET NULL
    op.drop_constraint('requisitions_retention_id_fkey', 'requisitions', type_='foreignkey')
    op.create_foreign_key('requisitions_retention_id_fkey', 'requisitions', 'retentions', ['retention_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Revert requisitions.retention_id
    op.drop_constraint('requisitions_retention_id_fkey', 'requisitions', type_='foreignkey')
    op.create_foreign_key('requisitions_retention_id_fkey', 'requisitions', 'retentions', ['retention_id'], ['id'])

    # Revert requisitions.supplier_id
    op.drop_constraint('requisitions_supplier_id_fkey', 'requisitions', type_='foreignkey')
    op.create_foreign_key('requisitions_supplier_id_fkey', 'requisitions', 'suppliers', ['supplier_id'], ['id'])

    # Revert supplier_documents.supplier_id
    op.drop_constraint('supplier_documents_supplier_id_fkey', 'supplier_documents', type_='foreignkey')
    op.create_foreign_key('supplier_documents_supplier_id_fkey', 'supplier_documents', 'suppliers', ['supplier_id'], ['id'])

    # Revert user_projects.project_id
    op.drop_constraint('user_projects_project_id_fkey', 'user_projects', type_='foreignkey')
    op.create_foreign_key('user_projects_project_id_fkey', 'user_projects', 'projects', ['project_id'], ['id'])

    # Revert user_projects.user_id
    op.drop_constraint('user_projects_user_id_fkey', 'user_projects', type_='foreignkey')
    op.create_foreign_key('user_projects_user_id_fkey', 'user_projects', 'users', ['user_id'], ['id'])
