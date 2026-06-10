"""add reports catalog and view permission

Revision ID: 20260525_100000
Revises: 20260525_000000
Create Date: 2026-05-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260525_100000'
down_revision: Union[str, None] = '20260525_000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO catalogs (catalog_code, catalog_name, description, is_active)
        SELECT 'reports', 'Reportes', 'Catálogo de reportes y exportaciones', true
        WHERE NOT EXISTS (SELECT 1 FROM catalogs WHERE catalog_code = 'reports')
    """)

    op.execute("""
        INSERT INTO actions (action_code, action_name, description, is_active)
        SELECT 'view', 'Ver', 'Permiso para ver/descargar reportes', true
        WHERE NOT EXISTS (SELECT 1 FROM actions WHERE action_code = 'view')
    """)

    op.execute("""
        INSERT INTO catalog_actions (catalog_id, action_id, is_active)
        SELECT c.id, a.id, true
        FROM catalogs c
        CROSS JOIN actions a
        WHERE c.catalog_code = 'reports'
          AND a.action_code = 'view'
          AND NOT EXISTS (
              SELECT 1 FROM catalog_actions ca
              WHERE ca.catalog_id = c.id AND ca.action_id = a.id
          )
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM catalog_actions
        WHERE catalog_id IN (SELECT id FROM catalogs WHERE catalog_code = 'reports')
          AND action_id IN (SELECT id FROM actions WHERE action_code = 'view')
    """)
    op.execute("DELETE FROM catalogs WHERE catalog_code = 'reports'")
