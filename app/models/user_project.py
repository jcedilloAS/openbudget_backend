from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserProject(Base):
    """UserProject association table model."""
    
    __tablename__ = "user_projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="assigned_projects")
    project = relationship("Project", back_populates="project_members")
    
    def __repr__(self):
        return f"<UserProject(id={self.id}, user_id={self.user_id}, project_id={self.project_id})>"
