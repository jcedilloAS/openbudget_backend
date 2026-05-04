from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    """Base schema for Category."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=255, description="Category description")
    is_active: bool = Field(default=True, description="Whether the category is active")


class CategoryCreate(CategoryBase):
    """Schema for creating a new Category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing Category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=255, description="Category description")
    is_active: Optional[bool] = Field(None, description="Whether the category is active")


class CategoryInDB(CategoryBase):
    """Schema for Category stored in database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDB):
    """Schema for Category response."""
    pass


class CategoryList(BaseModel):
    """Schema for paginated Category list."""
    total: int
    items: list[Category]
    
    model_config = ConfigDict(from_attributes=True)
