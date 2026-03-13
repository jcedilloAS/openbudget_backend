from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Catalog(Base):
    """Catalog database model."""
    
    __tablename__ = "catalogs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    catalog_code = Column(String(50), unique=True, index=True, nullable=False)
    catalog_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Catalog(id={self.id}, catalog_code='{self.catalog_code}', catalog_name='{self.catalog_name}')>"
