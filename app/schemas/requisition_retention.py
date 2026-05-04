from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class RetentionNested(BaseModel):
    """Minimal retention data embedded in requisition_retention responses."""
    id: int
    code: str
    description: Optional[str] = None
    percentage: Decimal
    is_active: bool
    due_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RequisitionRetentionInline(BaseModel):
    """Schema for inline retention when creating/updating a requisition."""
    retention_id: int = Field(..., gt=0, description="Retention ID")
    retention_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Calculated retention amount")


class RequisitionRetentionCreate(BaseModel):
    """Schema for creating a RequisitionRetention record."""
    requisition_id: int = Field(..., gt=0, description="Requisition ID")
    retention_id: int = Field(..., gt=0, description="Retention ID")
    retention_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Calculated retention amount")


class RequisitionRetentionUpdate(BaseModel):
    """Schema for updating retention_amount on an existing record."""
    retention_amount: Decimal = Field(..., ge=0, description="Updated retention amount")


class RequisitionRetentionInDB(BaseModel):
    """Schema for RequisitionRetention stored in database."""
    id: int
    requisition_id: int
    retention_id: int
    retention_amount: Decimal
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

    model_config = ConfigDict(from_attributes=True)


class RequisitionRetention(RequisitionRetentionInDB):
    """Schema for RequisitionRetention response with nested retention data."""
    retention: Optional[RetentionNested] = None

    model_config = ConfigDict(from_attributes=True)


class RequisitionRetentionList(BaseModel):
    """Schema for paginated RequisitionRetention list."""
    total: int
    items: list[RequisitionRetention]

    model_config = ConfigDict(from_attributes=True)
