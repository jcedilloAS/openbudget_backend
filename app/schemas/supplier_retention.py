from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class RetentionNested(BaseModel):
    """Minimal retention data embedded in supplier_retention responses."""
    id: int
    code: str
    description: Optional[str] = None
    percentage: Decimal
    is_active: bool
    due_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SupplierRetentionInline(BaseModel):
    """Schema for inline retention when creating/updating a supplier."""
    retention_id: int = Field(..., gt=0, description="Retention ID")


class SupplierRetentionCreate(BaseModel):
    """Schema for assigning a retention to a supplier."""
    supplier_id: int = Field(..., gt=0, description="Supplier ID")
    retention_id: int = Field(..., gt=0, description="Retention ID")


class SupplierRetentionInDB(BaseModel):
    """Schema for SupplierRetention stored in database."""
    id: int
    supplier_id: int
    retention_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

    model_config = ConfigDict(from_attributes=True)


class SupplierRetention(SupplierRetentionInDB):
    """Schema for SupplierRetention response with nested retention data."""
    retention: Optional[RetentionNested] = None

    model_config = ConfigDict(from_attributes=True)


class SupplierRetentionList(BaseModel):
    """Schema for paginated SupplierRetention list."""
    total: int
    items: list[SupplierRetention]

    model_config = ConfigDict(from_attributes=True)
