from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RequisitionDocument(Base):
    """RequisitionDocument database model."""

    __tablename__ = "requisition_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    document_url = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    requisition = relationship("Requisition", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by], backref="created_requisition_documents")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_requisition_documents")

    def __repr__(self):
        return f"<RequisitionDocument(id={self.id}, requisition_id={self.requisition_id})>"
