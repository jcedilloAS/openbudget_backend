from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """Audit Log database model."""
    
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    status = Column(String(20), nullable=False)
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    
    # Relationship
    user = relationship("User", backref="audit_logs")
    
    # Composite indexes for better query performance
    __table_args__ = (
        Index('ix_audit_log_user_date', 'user_id', 'date'),
        Index('ix_audit_log_module_date', 'module', 'date'),
        Index('ix_audit_log_action_module', 'action', 'module'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', module='{self.module}')>"
