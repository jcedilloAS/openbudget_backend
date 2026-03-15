from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from app.schemas.supplier_document import SupplierDocument


class SupplierBase(BaseModel):
    """Base schema for Supplier."""
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Unique supplier code")
    name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC (tax ID)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    percentage_iva: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days")
    is_active: bool = Field(default=True, description="Active status")


class SupplierCreate(BaseModel):
    """Schema for creating a new Supplier."""
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Unique supplier code")
    name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC (tax ID)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    percentage_iva: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days")
    is_active: bool = Field(default=True, description="Active status")


class SupplierUpdate(BaseModel):
    """Schema for updating an existing Supplier."""
    supplier_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique supplier code")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Supplier name")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC (tax ID)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    percentage_iva: Optional[Decimal] = Field(None, ge=0, le=100, description="IVA percentage")
    delivery_time_days: Optional[int] = Field(None, ge=0, description="Delivery time in days")
    is_active: Optional[bool] = Field(None, description="Active status")


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
    pass


class SupplierWithDocuments(Supplier):
    """Schema for Supplier response including child documents."""
    documents: List["SupplierDocument"] = []

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


# Resolve forward reference after SupplierDocument is importable
from app.schemas.supplier_document import SupplierDocument  # noqa: E402
SupplierWithDocuments.model_rebuild()
