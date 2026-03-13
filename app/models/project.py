from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Project(Base):
    """Project database model."""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    initial_budget = Column(Numeric(15, 2), nullable=False, default=0.00)
    commited = Column(Numeric(15, 2), nullable=False, default=0.00)
    spent = Column(Numeric(15, 2), nullable=False, default=0.00)
    available_balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    status = Column(String(50), nullable=False, default="pendiente")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_projects")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_projects")
    
    # Many-to-many relationship with users through user_projects
    project_members = relationship("UserProject", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, project_code='{self.project_code}', name='{self.name}')>"
