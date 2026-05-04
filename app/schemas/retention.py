from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class RetentionBase(BaseModel):
    """Base schema for Retention."""
    code: str = Field(..., min_length=1, max_length=50, description="Unique retention code")
    description: Optional[str] = Field(None, max_length=255, description="Retention description")
    percentage: Decimal = Field(..., ge=0, le=100, description="Retention percentage (0-100)")
    is_active: bool = Field(default=True, description="Whether the retention is active")
    due_date: Optional[datetime] = Field(None, description="Due date for the retention")


class RetentionCreate(RetentionBase):
    """Schema for creating a new Retention."""
    pass


class RetentionUpdate(BaseModel):
    """Schema for updating an existing Retention."""
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique retention code")
    description: Optional[str] = Field(None, max_length=255, description="Retention description")
    percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Retention percentage (0-100)")
    is_active: Optional[bool] = Field(None, description="Whether the retention is active")
    due_date: Optional[datetime] = Field(None, description="Due date for the retention")


class RetentionInDB(RetentionBase):
    """Schema for Retention stored in database."""
    id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    
    model_config = ConfigDict(from_attributes=True)


class Retention(RetentionInDB):
    """Schema for Retention response."""
    pass


class RetentionList(BaseModel):
    """Schema for paginated Retention list."""
    total: int
    items: list[Retention]
    
    model_config = ConfigDict(from_attributes=True)
