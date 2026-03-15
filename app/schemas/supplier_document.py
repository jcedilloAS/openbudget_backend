from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class SupplierDocumentBase(BaseModel):
    """Base schema for SupplierDocument."""
    supplier_id: int = Field(..., gt=0, description="Supplier ID")
    description: Optional[str] = Field(None, max_length=500, description="Document description")
    document_url: str = Field(..., min_length=1, max_length=1000, description="Document URL")


class SupplierDocumentCreate(SupplierDocumentBase):
    """Schema for creating a new SupplierDocument."""
    created_by: int = Field(..., gt=0, description="User ID who created the document")
    updated_by: int = Field(..., gt=0, description="User ID who last updated the document")


class SupplierDocumentUpdate(BaseModel):
    """Schema for updating an existing SupplierDocument."""
    description: Optional[str] = Field(None, max_length=500, description="Document description")
    document_url: Optional[str] = Field(None, min_length=1, max_length=1000, description="Document URL")
    updated_by: int = Field(..., gt=0, description="User ID who is updating the document")


class SupplierDocumentInDB(SupplierDocumentBase):
    """Schema for SupplierDocument stored in database."""
    id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

    model_config = ConfigDict(from_attributes=True)


class SupplierDocument(SupplierDocumentInDB):
    """Schema for SupplierDocument response."""
    pass


class SupplierDocumentList(BaseModel):
    """Schema for paginated SupplierDocument list."""
    total: int
    items: list[SupplierDocument]

    model_config = ConfigDict(from_attributes=True)
