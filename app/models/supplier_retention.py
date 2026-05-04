from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SupplierRetention(Base):
    """Association table between Supplier and Retention."""

    __tablename__ = "supplier_retentions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    retention_id = Column(Integer, ForeignKey("retentions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("supplier_id", "retention_id", name="uq_supplier_retention"),
    )

    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_retentions")
    retention = relationship("Retention", foreign_keys=[retention_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<SupplierRetention(id={self.id}, supplier_id={self.supplier_id}, retention_id={self.retention_id})>"
