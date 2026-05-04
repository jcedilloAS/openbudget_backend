from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class RequisitionDocumentInline(BaseModel):
    """Schema for inline document data when creating/updating a requisition."""
    id: Optional[int] = Field(None, gt=0, description="Document ID (for updates, omit for new documents)")
    description: Optional[str] = Field(None, max_length=500, description="Document description")
    document_url: Optional[str] = Field(None, min_length=1, max_length=1000, description="Document URL (required for new docs, optional when updating existing)")


class RequisitionDocumentBase(BaseModel):
    """Base schema for RequisitionDocument."""
    requisition_id: int = Field(..., gt=0, description="Requisition ID")
    description: Optional[str] = Field(None, max_length=500, description="Document description")
    document_url: str = Field(..., min_length=1, max_length=1000, description="Document URL")


class RequisitionDocumentCreate(RequisitionDocumentBase):
    """Schema for creating a new RequisitionDocument."""
    created_by: int = Field(..., gt=0, description="User ID who created the document")
    updated_by: int = Field(..., gt=0, description="User ID who last updated the document")


class RequisitionDocumentUpdate(BaseModel):
    """Schema for updating an existing RequisitionDocument."""
    description: Optional[str] = Field(None, max_length=500, description="Document description")
    document_url: Optional[str] = Field(None, min_length=1, max_length=1000, description="Document URL")
    updated_by: int = Field(..., gt=0, description="User ID who is updating the document")


class RequisitionDocumentInDB(RequisitionDocumentBase):
    """Schema for RequisitionDocument stored in database."""
    id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

    model_config = ConfigDict(from_attributes=True)


class RequisitionDocument(RequisitionDocumentInDB):
    """Schema for RequisitionDocument response."""
    pass


class RequisitionDocumentList(BaseModel):
    """Schema for paginated RequisitionDocument list."""
    total: int
    items: list[RequisitionDocument]

    model_config = ConfigDict(from_attributes=True)
