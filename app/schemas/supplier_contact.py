from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional


class SupplierContactInline(BaseModel):
    """Schema for inline contact data within supplier create/update."""
    id: Optional[int] = Field(None, description="Contact ID (omit for new contacts)")
    name: str = Field(..., min_length=1, max_length=200, description="Contact name")
    email: Optional[str] = Field(None, max_length=200, description="Contact email")
    telephone: Optional[str] = Field(None, max_length=50, description="Contact telephone")
    address: Optional[str] = Field(None, max_length=500, description="Contact address")


class SupplierContactInDB(BaseModel):
    """Schema for SupplierContact stored in database."""
    id: int
    supplier_id: int
    name: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

    model_config = ConfigDict(from_attributes=True)


class SupplierContact(SupplierContactInDB):
    """Schema for SupplierContact response."""
    model_config = ConfigDict(from_attributes=True)
