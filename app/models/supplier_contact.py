from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SupplierContact(Base):
    """SupplierContact database model."""

    __tablename__ = "supplier_contacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    telephone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="contacts")
    creator = relationship("User", foreign_keys=[created_by], backref="created_supplier_contacts")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_supplier_contacts")

    def __repr__(self):
        return f"<SupplierContact(id={self.id}, supplier_id={self.supplier_id}, name='{self.name}')>"
