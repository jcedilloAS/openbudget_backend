from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Requisition(Base):
    """Requisition database model."""
    
    __tablename__ = "requisitions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_number = Column(String(50), unique=True, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    currency = Column(String(10), nullable=False, default="MXN")
    exchange_rate = Column(Numeric(10, 4), nullable=False, default=1.0000)
    subtotal = Column(Numeric(15, 2), nullable=False, default=0.00)
    iva_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    iva_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    retention_id = Column(Integer, ForeignKey("retentions.id", ondelete="SET NULL"), nullable=True)
    retention_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    status = Column(String(50), nullable=False, default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id], backref="requisitions")
    supplier = relationship("Supplier", foreign_keys=[supplier_id], backref="requisitions")
    retention = relationship("Retention", foreign_keys=[retention_id], backref="requisitions")
    requester = relationship("User", foreign_keys=[requested_by], backref="requested_requisitions")
    approver = relationship("User", foreign_keys=[approved_by], backref="approved_requisitions")
    rejector = relationship("User", foreign_keys=[rejected_by], backref="rejected_requisitions")
    creator = relationship("User", foreign_keys=[created_by], backref="created_requisitions")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_requisitions")
    items = relationship("RequisitionItem", back_populates="requisition", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Requisition(id={self.id}, requisition_number='{self.requisition_number}', status='{self.status}')>"
