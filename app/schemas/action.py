from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ActionBase(BaseModel):
    """Base schema for Action."""
    action_code: str = Field(..., min_length=1, max_length=50, description="Unique action code")
    action_name: str = Field(..., min_length=1, max_length=100, description="Action name")
    description: Optional[str] = Field(None, max_length=255, description="Action description")
    is_active: bool = Field(default=True, description="Whether the action is active")


class ActionCreate(ActionBase):
    """Schema for creating a new Action."""
    pass


class ActionUpdate(BaseModel):
    """Schema for updating an existing Action."""
    action_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique action code")
    action_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Action name")
    description: Optional[str] = Field(None, max_length=255, description="Action description")
    is_active: Optional[bool] = Field(None, description="Whether the action is active")


class ActionInDB(ActionBase):
    """Schema for Action stored in database."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Action(ActionInDB):
    """Schema for Action response."""
    pass


class ActionList(BaseModel):
    """Schema for paginated Action list."""
    total: int
    items: list[Action]
    
    model_config = ConfigDict(from_attributes=True)
