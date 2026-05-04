from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from app.schemas.requisition_item import RequisitionItemInline, RequisitionItem, RequisitionItemAccountAssignment
from app.schemas.requisition_document import RequisitionDocumentInline
from app.schemas.requisition_retention import RequisitionRetentionInline


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
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Total amount")
    status: str = Field(default="draft", max_length=50, description="Status (draft, submitted, approved, rejected, cancelled)")
    purchase_order: Optional[str] = Field(None, max_length=100, description="Purchase order number")


class RequisitionCreate(BaseModel):
    """Schema for creating a new Requisition."""
    requisition_number: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique requisition number (auto-generated if omitted)")
    project_id: int = Field(..., gt=0, description="Project ID")
    supplier_id: int = Field(None, gt=0, description="Supplier ID")
    requested_by: Optional[int] = Field(None, gt=0, description="User ID who requested")
    currency: str = Field(default="MXN", min_length=3, max_length=10, description="Currency code")
    exchange_rate: Decimal = Field(default=Decimal("1.0000"), ge=0, description="Exchange rate")
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0, description="Subtotal amount")
    iva_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="IVA percentage")
    iva_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="IVA amount")
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Total amount")
    status: str = Field(default="draft", max_length=50, description="Status (draft, submitted, approved, rejected, cancelled)")
    purchase_order: Optional[str] = Field(None, max_length=100, description="Purchase order number")
    items: Optional[List[RequisitionItemInline]] = Field(None, description="List of requisition items")
    documents: Optional[List[RequisitionDocumentInline]] = Field(None, description="List of documents to attach")
    retentions: Optional[List[RequisitionRetentionInline]] = Field(None, description="List of retentions to apply")


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
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount")
    status: Optional[str] = Field(None, max_length=50, description="Status (pending, approved, rejected)")
    purchase_order: Optional[str] = Field(None, max_length=100, description="Purchase order number")
    items: Optional[List[RequisitionItemInline]] = Field(None, description="List of requisition items")
    documents: Optional[List[RequisitionDocumentInline]] = Field(None, description="List of documents to attach or keep")
    retentions: Optional[List[RequisitionRetentionInline]] = Field(None, description="List of retentions to apply (replaces existing)")

    model_config = ConfigDict(from_attributes=True)


class RequisitionApprove(BaseModel):
    """Schema para aprobar una requisición."""
    item_account_assignments: Optional[List[RequisitionItemAccountAssignment]] = Field(
        None, description="Asignaciones de cuenta contable por item (item_id → account_id)"
    )


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
    supplier_name: Optional[str] = Field(None, description="Supplier name")
    created_by_name: Optional[str] = Field(None, description="Name of the user who created the requisition")

    @model_validator(mode='before')
    @classmethod
    def populate_related_names(cls, data):
        if not isinstance(data, dict):
            supplier = getattr(data, 'supplier', None)
            creator = getattr(data, 'creator', None)
            data.__dict__['supplier_name'] = supplier.name if supplier else None
            data.__dict__['created_by_name'] = creator.name if creator else None
        return data

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


class RequisitionWithDocuments(RequisitionWithDetails):
    """Schema for Requisition response including items, documents and retentions."""
    documents: List["RequisitionDocument"] = []
    retentions: List["RequisitionRetention"] = []

    model_config = ConfigDict(from_attributes=True)


from app.schemas.requisition_document import RequisitionDocument  # noqa: E402
from app.schemas.requisition_retention import RequisitionRetention  # noqa: E402
RequisitionWithDocuments.model_rebuild()
