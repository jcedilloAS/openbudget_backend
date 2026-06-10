from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date, datetime
from typing import Literal, Optional, List, TYPE_CHECKING
from decimal import Decimal

from app.schemas.supplier_document import SupplierDocumentInline
from app.schemas.supplier_retention import SupplierRetentionInline
from app.schemas.supplier_contact import SupplierContactInline

if TYPE_CHECKING:
    from app.schemas.supplier_document import SupplierDocument
    from app.schemas.supplier_contact import SupplierContact as SupplierContactSchema


class SupplierBase(BaseModel):
    """Base schema for Supplier."""
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Unique supplier code")
    name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    origin: Optional[Literal["NACIONAL", "EXTRANJERA"]] = Field(None, description="Supplier origin")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC (tax ID)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    percentage_iva: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    isr_withheld_professional_fees: Optional[Decimal] = Field(None, ge=0, le=100, description="ISR withheld rate for professional fees (honorarios)")
    isr_withheld_resico: Optional[Decimal] = Field(None, ge=0, le=100, description="ISR withheld rate for RESICO taxpayers")
    iva_withheld_professional_fees: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for professional fees (honorarios)")
    iva_withheld_resico: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for RESICO taxpayers")
    iva_withheld_freight: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for freight services (fletes)")
    tax_start_date: Optional[date] = Field(None, description="Tax rates validity start date")
    tax_end_date: Optional[date] = Field(None, description="Tax rates validity end date")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days")
    category_id: Optional[int] = Field(None, description="Category ID")
    is_active: bool = Field(default=True, description="Active status")

    @model_validator(mode="after")
    def validate_tax_dates(self):
        if self.tax_start_date and self.tax_end_date and self.tax_end_date < self.tax_start_date:
            raise ValueError("tax_end_date must be on or after tax_start_date")
        return self


class SupplierCreate(BaseModel):
    """Schema for creating a new Supplier."""
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Unique supplier code")
    name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    origin: Optional[Literal["NACIONAL", "EXTRANJERA"]] = Field(None, description="Supplier origin")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC (tax ID)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    percentage_iva: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    isr_withheld_professional_fees: Optional[Decimal] = Field(None, ge=0, le=100, description="ISR withheld rate for professional fees (honorarios)")
    isr_withheld_resico: Optional[Decimal] = Field(None, ge=0, le=100, description="ISR withheld rate for RESICO taxpayers")
    iva_withheld_professional_fees: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for professional fees (honorarios)")
    iva_withheld_resico: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for RESICO taxpayers")
    iva_withheld_freight: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for freight services (fletes)")
    tax_start_date: Optional[date] = Field(None, description="Tax rates validity start date")
    tax_end_date: Optional[date] = Field(None, description="Tax rates validity end date")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days")
    category_id: Optional[int] = Field(None, description="Category ID")
    is_active: bool = Field(default=True, description="Active status")
    documents: Optional[List[SupplierDocumentInline]] = Field(None, description="List of supplier documents")
    retentions: Optional[List[SupplierRetentionInline]] = Field(None, description="List of retentions to assign")
    contacts: Optional[List[SupplierContactInline]] = Field(None, description="List of supplier contacts")


class SupplierUpdate(BaseModel):
    """Schema for updating an existing Supplier."""
    supplier_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique supplier code")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Supplier name")
    origin: Optional[Literal["NACIONAL", "EXTRANJERA"]] = Field(None, description="Supplier origin")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC (tax ID)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    percentage_iva: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    isr_withheld_professional_fees: Optional[Decimal] = Field(None, ge=0, le=100, description="ISR withheld rate for professional fees (honorarios)")
    isr_withheld_resico: Optional[Decimal] = Field(None, ge=0, le=100, description="ISR withheld rate for RESICO taxpayers")
    iva_withheld_professional_fees: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for professional fees (honorarios)")
    iva_withheld_resico: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for RESICO taxpayers")
    iva_withheld_freight: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA withheld rate for freight services (fletes)")
    tax_start_date: Optional[date] = Field(None, description="Tax rates validity start date")
    tax_end_date: Optional[date] = Field(None, description="Tax rates validity end date")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days")
    category_id: Optional[int] = Field(None, description="Category ID")
    is_active: Optional[bool] = Field(None, description="Active status")
    documents: Optional[List[SupplierDocumentInline]] = Field(None, description="List of supplier documents")
    retentions: Optional[List[SupplierRetentionInline]] = Field(None, description="List of retentions to assign (replaces existing)")
    contacts: Optional[List[SupplierContactInline]] = Field(None, description="List of supplier contacts (replaces existing)")


class SupplierInDB(SupplierBase):
    """Schema for Supplier stored in database."""
    id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    
    model_config = ConfigDict(from_attributes=True)


class Supplier(SupplierInDB):
    """Schema for Supplier response."""
    category_name: Optional[str] = Field(None, description="Category name")
    
    model_config = ConfigDict(from_attributes=True)


class SupplierWithDocuments(Supplier):
    """Schema for Supplier response including child documents, retentions and contacts."""
    documents: List["SupplierDocument"] = []
    supplier_retentions: List["SupplierRetentionSchema"] = []
    contacts: List["SupplierContactSchema"] = []

    model_config = ConfigDict(from_attributes=True)


class SupplierWithUsers(Supplier):
    """Schema for Supplier response with creator and updater details."""
    creator: Optional[dict] = None
    updater: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class SupplierList(BaseModel):
    """Schema for paginated Supplier list."""
    total: int
    items: list[Supplier]

    model_config = ConfigDict(from_attributes=True)


# Resolve forward references
from app.schemas.supplier_document import SupplierDocument  # noqa: E402
from app.schemas.supplier_retention import SupplierRetention as SupplierRetentionSchema  # noqa: E402
from app.schemas.supplier_contact import SupplierContact as SupplierContactSchema  # noqa: E402
SupplierWithDocuments.model_rebuild()
