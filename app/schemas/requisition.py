from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from app.schemas.requisition_item import RequisitionItemInline, RequisitionItem


class RequisitionBase(BaseModel):
    """Base schema for Requisition."""
    requisition_number: str = Field(..., min_length=1, max_length=50, description="Unique requisition number")
    project_id: int = Field(..., gt=0, description="Project ID")
    supplier_id: Optional[int] = Field(None, gt=0, description="Supplier ID")
    requested_by: Optional[int] = Field(None, gt=0, description="User ID who requested")
    currency: str = Field(default="MXN", min_length=3, max_length=10, description="Currency code")
    exchange_rate: Decimal = Field(default=Decimal("1.0000"), ge=0, description="Exchange rate")
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0, description="Subtotal amount")
    iva_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="IVA percentage")
    iva_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="IVA amount")
    retention_id: Optional[int] = Field(None, gt=0, description="Retention ID")
    retention_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Retention amount")
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Total amount")
    status: str = Field(default="draft", max_length=50, description="Status (draft, submitted, approved, rejected, cancelled)")


class RequisitionCreate(BaseModel):
    """Schema for creating a new Requisition."""
    requisition_number: str = Field(..., min_length=1, max_length=50, description="Unique requisition number")
    project_id: int = Field(..., gt=0, description="Project ID")
    supplier_id: int = Field(None, gt=0, description="Supplier ID")
    requested_by: Optional[int] = Field(None, gt=0, description="User ID who requested")
    currency: str = Field(default="MXN", min_length=3, max_length=10, description="Currency code")
    exchange_rate: Decimal = Field(default=Decimal("1.0000"), ge=0, description="Exchange rate")
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0, description="Subtotal amount")
    iva_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="IVA percentage")
    iva_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="IVA amount")
    retention_id: Optional[int] = Field(None, gt=0, description="Retention ID")
    retention_amount: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0, description="Retention amount")
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Total amount")
    status: str = Field(default="draft", max_length=50, description="Status (draft, submitted, approved, rejected, cancelled)")
    items: Optional[List[RequisitionItemInline]] = Field(None, description="List of requisition items")


class RequisitionUpdate(BaseModel):
    """Schema for updating an existing Requisition."""
    requisition_number: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique requisition number")
    project_id: Optional[int] = Field(None, gt=0, description="Project ID")
    supplier_id: Optional[int] = Field(None, gt=0, description="Supplier ID")
    requested_by: Optional[int] = Field(None, gt=0, description="User ID who requested")
    currency: Optional[str] = Field(None, min_length=3, max_length=10, description="Currency code")
    exchange_rate: Optional[Decimal] = Field(None, ge=0, description="Exchange rate")
    subtotal: Optional[Decimal] = Field(None, ge=0, description="Subtotal amount")
    iva_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    iva_amount: Optional[Decimal] = Field(None, ge=0, description="IVA amount")
    retention_id: Optional[int] = Field(None, gt=0, description="Retention ID")
    retention_amount: Optional[Decimal] = Field(None, ge=0, description="Retention amount")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount")
    status: Optional[str] = Field(None, max_length=50, description="Status (pending, approved, rejected)")
    items: Optional[List[RequisitionItemInline]] = Field(None, description="List of requisition items")
    
    model_config = ConfigDict(from_attributes=True)


class RequisitionApprove(BaseModel):
    """Schema for approving a requisition."""
    pass


class RequisitionReject(BaseModel):
    """Schema for rejecting a requisition."""
    rejection_reason: str = Field(..., min_length=1, max_length=500, description="Reason for rejection")


class Requisition(RequisitionBase):
    """Schema for Requisition response."""
    id: int = Field(..., description="Requisition ID")
    approved_by: Optional[int] = Field(None, description="User ID who approved")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejected_by: Optional[int] = Field(None, description="User ID who rejected")
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: int = Field(..., description="User ID who created")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: int = Field(..., description="User ID who last updated")
    
    model_config = ConfigDict(from_attributes=True)


class RequisitionList(BaseModel):
    """Schema for Requisition list response with pagination."""
    total: int = Field(..., description="Total number of requisitions")
    items: List[Requisition] = Field(..., description="List of requisitions")
    
    model_config = ConfigDict(from_attributes=True)


class RequisitionWithDetails(Requisition):
    """Schema for Requisition response with related data."""
    items: Optional[List[RequisitionItem]] = Field(None, description="List of requisition items")
    
    model_config = ConfigDict(from_attributes=True)
