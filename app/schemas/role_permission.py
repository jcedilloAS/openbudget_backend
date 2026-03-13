from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class RolePermissionBase(BaseModel):
    """Base schema for RolePermission."""
    role_id: int = Field(..., description="Role ID")
    catalog_action_id: int = Field(..., description="Catalog-Action ID")
    is_allowed: bool = Field(default=True, description="Whether the permission is allowed or denied")


class RolePermissionCreate(RolePermissionBase):
    """Schema for creating a new RolePermission."""
    pass


class RolePermissionUpdate(BaseModel):
    """Schema for updating an existing RolePermission."""
    is_allowed: Optional[bool] = Field(None, description="Whether the permission is allowed or denied")


class RolePermissionInDB(RolePermissionBase):
    """Schema for RolePermission stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RolePermission(RolePermissionInDB):
    """Schema for RolePermission response."""
    pass


class RolePermissionWithDetails(RolePermissionInDB):
    """Schema for RolePermission with role, catalog and action details."""
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    catalog_code: Optional[str] = None
    catalog_name: Optional[str] = None
    action_code: Optional[str] = None
    action_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RolePermissionList(BaseModel):
    """Schema for paginated RolePermission list."""
    total: int
    items: list[RolePermission]
    
    model_config = ConfigDict(from_attributes=True)


class RolePermissionListWithDetails(BaseModel):
    """Schema for paginated RolePermission list with details."""
    total: int
    items: list[RolePermissionWithDetails]
    
    model_config = ConfigDict(from_attributes=True)


class RolePermissionBulkCreate(BaseModel):
    """Schema for bulk creating permissions for a role."""
    role_id: int = Field(..., description="Role ID")
    catalog_action_ids: list[int] = Field(..., description="List of Catalog-Action IDs")
    is_allowed: bool = Field(default=True, description="Whether the permissions are allowed or denied")
