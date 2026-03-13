from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CatalogAction(Base):
    """CatalogAction database model - Links catalogs with actions."""
    
    __tablename__ = "catalog_actions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    catalog_id = Column(Integer, ForeignKey('catalogs.id', ondelete='CASCADE'), nullable=False)
    action_id = Column(Integer, ForeignKey('actions.id', ondelete='CASCADE'), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    catalog = relationship("Catalog", backref="catalog_actions")
    action = relationship("Action", backref="catalog_actions")
    
    # Unique constraint to avoid duplicates
    __table_args__ = (
        UniqueConstraint('catalog_id', 'action_id', name='uq_catalog_action'),
    )
    
    def __repr__(self):
        return f"<CatalogAction(id={self.id}, catalog_id={self.catalog_id}, action_id={self.action_id})>"
