from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SupplierDocument(Base):
    """SupplierDocument database model."""

    __tablename__ = "supplier_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    document_url = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by], backref="created_supplier_documents")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_supplier_documents")

    def __repr__(self):
        return f"<SupplierDocument(id={self.id}, supplier_id={self.supplier_id})>"
