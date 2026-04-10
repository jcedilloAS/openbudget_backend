from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class RequisitionItemBase(BaseModel):
    """Base schema for RequisitionItem."""
    item_name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    total_amount: Decimal = Field(..., ge=0, description="Total amount")


class RequisitionItemCreate(BaseModel):
    """Schema for creating a new RequisitionItem."""
    item_name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    total_amount: Decimal = Field(..., ge=0, description="Total amount")


class RequisitionItemUpdate(BaseModel):
    """Schema for updating an existing RequisitionItem."""
    item_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    quantity: Optional[Decimal] = Field(None, gt=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Unit price")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount")
    
    model_config = ConfigDict(from_attributes=True)


class RequisitionItem(RequisitionItemBase):
    """Schema for RequisitionItem response."""
    id: int = Field(..., description="Item ID")
    requisition_id: int = Field(..., description="Requisition ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RequisitionItemList(BaseModel):
    """Schema for RequisitionItem list response with pagination."""
    total: int = Field(..., description="Total number of items")
    items: List[RequisitionItem] = Field(..., description="List of requisition items")
    
    model_config = ConfigDict(from_attributes=True)


class RequisitionItemInline(BaseModel):
    """Schema for inline RequisitionItem (used in Requisition creation/update)."""
    id: Optional[int] = Field(None, description="Item ID (for updates)")
    item_name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    total_amount: Decimal = Field(..., ge=0, description="Total amount")
    
    model_config = ConfigDict(from_attributes=True)
