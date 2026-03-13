from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CatalogBase(BaseModel):
    """Base schema for Catalog."""
    catalog_code: str = Field(..., min_length=1, max_length=50, description="Unique catalog code")
    catalog_name: str = Field(..., min_length=1, max_length=100, description="Catalog name")
    description: Optional[str] = Field(None, max_length=255, description="Catalog description")
    is_active: bool = Field(default=True, description="Whether the catalog is active")


class CatalogCreate(CatalogBase):
    """Schema for creating a new Catalog."""
    pass


class CatalogUpdate(BaseModel):
    """Schema for updating an existing Catalog."""
    catalog_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique catalog code")
    catalog_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Catalog name")
    description: Optional[str] = Field(None, max_length=255, description="Catalog description")
    is_active: Optional[bool] = Field(None, description="Whether the catalog is active")


class CatalogInDB(CatalogBase):
    """Schema for Catalog stored in database."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Catalog(CatalogInDB):
    """Schema for Catalog response."""
    pass


class CatalogList(BaseModel):
    """Schema for paginated Catalog list."""
    total: int
    items: list[Catalog]
    
    model_config = ConfigDict(from_attributes=True)
