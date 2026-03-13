from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RolePermission(Base):
    """RolePermission database model - Links roles with catalog_actions for permissions."""
    
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    catalog_action_id = Column(Integer, ForeignKey('catalog_actions.id', ondelete='CASCADE'), nullable=False)
    is_allowed = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    role = relationship("Role", backref="role_permissions")
    catalog_action = relationship("CatalogAction", backref="role_permissions")
    
    # Unique constraint to avoid duplicate permissions
    __table_args__ = (
        UniqueConstraint('role_id', 'catalog_action_id', name='uq_role_catalog_action'),
    )
    
    def __repr__(self):
        return f"<RolePermission(id={self.id}, role_id={self.role_id}, catalog_action_id={self.catalog_action_id}, is_allowed={self.is_allowed})>"
