from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RequisitionRetention(Base):
    """Retentions applied to a requisition."""

    __tablename__ = "requisition_retentions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False, index=True)
    retention_id = Column(Integer, ForeignKey("retentions.id", ondelete="CASCADE"), nullable=False, index=True)
    retention_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("requisition_id", "retention_id", name="uq_requisition_retention"),
    )

    # Relationships
    requisition = relationship("Requisition", back_populates="retentions")
    retention = relationship("Retention", foreign_keys=[retention_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<RequisitionRetention(id={self.id}, requisition_id={self.requisition_id}, retention_id={self.retention_id})>"
