from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserProjectBase(BaseModel):
    """Base schema for UserProject."""
    user_id: int = Field(..., gt=0, description="User ID")
    project_id: int = Field(..., gt=0, description="Project ID")


class UserProjectCreate(UserProjectBase):
    """Schema for creating a new UserProject association."""
    pass


class UserProjectInDB(UserProjectBase):
    """Schema for UserProject stored in database."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserProject(UserProjectInDB):
    """Schema for UserProject response."""
    pass


class UserProjectWithDetails(UserProject):
    """Schema for UserProject response with user and project details."""
    user: Optional[dict] = None
    project: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserProjectList(BaseModel):
    """Schema for paginated UserProject list."""
    total: int
    items: list[UserProject]
    
    model_config = ConfigDict(from_attributes=True)
