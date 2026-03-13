from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CatalogActionBase(BaseModel):
    """Base schema for CatalogAction."""
    catalog_id: int = Field(..., description="Catalog ID")
    action_id: int = Field(..., description="Action ID")
    is_active: bool = Field(default=True, description="Whether the catalog-action relationship is active")


class CatalogActionCreate(CatalogActionBase):
    """Schema for creating a new CatalogAction."""
    pass


class CatalogActionUpdate(BaseModel):
    """Schema for updating an existing CatalogAction."""
    is_active: Optional[bool] = Field(None, description="Whether the catalog-action relationship is active")


class CatalogActionInDB(CatalogActionBase):
    """Schema for CatalogAction stored in database."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CatalogAction(CatalogActionInDB):
    """Schema for CatalogAction response."""
    pass


class CatalogActionWithDetails(CatalogActionInDB):
    """Schema for CatalogAction with catalog and action details."""
    catalog_code: Optional[str] = None
    catalog_name: Optional[str] = None
    action_code: Optional[str] = None
    action_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class CatalogActionList(BaseModel):
    """Schema for paginated CatalogAction list."""
    total: int
    items: list[CatalogAction]
    
    model_config = ConfigDict(from_attributes=True)


class CatalogActionListWithDetails(BaseModel):
    """Schema for paginated CatalogAction list with details."""
    total: int
    items: list[CatalogActionWithDetails]
    
    model_config = ConfigDict(from_attributes=True)
