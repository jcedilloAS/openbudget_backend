from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class RoleBase(BaseModel):
    """Base schema for Role."""
    role_code: str = Field(..., min_length=1, max_length=50, description="Unique role code")
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=255, description="Role description")
    is_active: bool = Field(default=True, description="Whether the role is active")


class RoleCreate(RoleBase):
    """Schema for creating a new Role."""
    catalog_action_ids: Optional[list[int]] = Field(None, description="List of catalog-action IDs to assign as permissions")


class RoleUpdate(BaseModel):
    """Schema for updating an existing Role."""
    role_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Unique role code")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=255, description="Role description")
    is_active: Optional[bool] = Field(None, description="Whether the role is active")
    catalog_action_ids: Optional[list[int]] = Field(None, description="List of catalog-action IDs to replace current permissions")


class RoleInDB(RoleBase):
    """Schema for Role stored in database."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Role(RoleInDB):
    """Schema for Role response."""
    pass


class PermissionDetail(BaseModel):
    """Schema for permission details."""
    catalog_action_id: int = Field(..., description="Catalog-Action ID")
    catalog_id: int = Field(..., description="Catalog ID")
    catalog_name: str = Field(..., description="Catalog name")
    catalog_code: str = Field(..., description="Catalog code")
    action_id: int = Field(..., description="Action ID")
    action_name: str = Field(..., description="Action name")
    action_code: str = Field(..., description="Action code")
    
    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissions(RoleInDB):
    """Schema for Role with detailed permissions."""
    permissions: Optional[list[PermissionDetail]] = Field(None, description="List of permissions with catalog and action details")
    
    model_config = ConfigDict(from_attributes=True)


class RoleList(BaseModel):
    """Schema for paginated Role list."""
    total: int
    items: list[Role]
    
    model_config = ConfigDict(from_attributes=True)
