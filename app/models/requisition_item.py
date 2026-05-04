from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RequisitionItem(Base):
    """Requisition Item database model."""

    __tablename__ = "requisition_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    item_name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(15, 4), nullable=False, default=0.0000)
    unit = Column(String(50), nullable=True)
    unit_price = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    requisition = relationship("Requisition", back_populates="items")
    account = relationship("Account", foreign_keys=[account_id])
    
    def __repr__(self):
        return f"<RequisitionItem(id={self.id}, requisition_id={self.requisition_id}, item_name='{self.item_name}')>"
