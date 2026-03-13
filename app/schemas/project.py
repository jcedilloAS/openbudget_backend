from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class ProjectBase(BaseModel):
    """Base schema for Project."""
    project_code: str = Field(..., min_length=1, max_length=50, description="Unique project code")
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    initial_budget: Decimal = Field(default=Decimal("0.00"), ge=0, description="Initial budget amount")
    commited: Decimal = Field(default=Decimal("0.00"), ge=0, description="Committed amount")
    spent: Decimal = Field(default=Decimal("0.00"), ge=0, description="Spent amount")
    available_balance: Decimal = Field(default=Decimal("0.00"), ge=0, description="Available balance")
    status: str = Field(default="ACTIVE", max_length=50, description="Project status")


class ProjectCreate(BaseModel):
    """Schema for creating a new Project."""
    project_code: str = Field(..., min_length=1, max_length=50, description="Unique project code")
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    initial_budget: Decimal = Field(default=Decimal("0.00"), ge=0, description="Initial budget amount")
    commited: Decimal = Field(default=Decimal("0.00"), ge=0, description="Committed amount")
    spent: Decimal = Field(default=Decimal("0.00"), ge=0, description="Spent amount")
    available_balance: Decimal = Field(default=Decimal("0.00"), ge=0, description="Available balance")
    status: str = Field(default="ACTIVE", max_length=50, description="Project status")
    user_ids: Optional[List[int]] = Field(default=None, description="List of user IDs to assign to the project")


class ProjectUpdate(BaseModel):
    """Schema for updating an existing Project."""
    project_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique project code")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    initial_budget: Optional[Decimal] = Field(None, ge=0, description="Initial budget amount")
    commited: Optional[Decimal] = Field(None, ge=0, description="Committed amount")
    spent: Optional[Decimal] = Field(None, ge=0, description="Spent amount")
    user_ids: Optional[List[int]] = Field(None, description="List of user IDs to assign to the project")
    available_balance: Optional[Decimal] = Field(None, ge=0, description="Available balance")
    status: Optional[str] = Field(None, max_length=50, description="Project status")


class ProjectInDB(ProjectBase):
    """Schema for Project stored in database."""
    id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    
    model_config = ConfigDict(from_attributes=True)


class Project(ProjectInDB):
    """Schema for Project response."""
    pass


class ProjectWithUsers(Project):
    """Schema for Project response with creator and updater details."""
    creator: Optional[dict] = None
    updater: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    """Schema for paginated Project list."""
    total: int
    items: list[Project]
    
    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    """Schema for project budget summary."""
    total_projects: int
    total_initial_budget: Decimal
    total_commited: Decimal
    total_spent: Decimal
    total_available: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class ProjectMemberSimple(BaseModel):
    """Schema for project member (simplified user info)."""
    id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProjectWithMembers(Project):
    """Schema for Project response with team members."""
    project_members: Optional[list[ProjectMemberSimple]] = None
    
    model_config = ConfigDict(from_attributes=True)
