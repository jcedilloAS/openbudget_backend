from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Action(Base):
    """Action database model."""
    
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action_code = Column(String(50), unique=True, index=True, nullable=False)
    action_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Action(id={self.id}, action_code='{self.action_code}', action_name='{self.action_name}')>"
