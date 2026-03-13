from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class AuditLogBase(BaseModel):
    """Base schema for AuditLog."""
    user_id: int = Field(..., gt=0, description="User ID who performed the action")
    action: str = Field(..., min_length=1, max_length=50, description="Action performed (CREATE, UPDATE, DELETE, etc.)")
    module: str = Field(..., min_length=1, max_length=100, description="Module/table affected")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the action")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address of the user")
    status: str = Field(..., min_length=1, max_length=20, description="Status of the action (SUCCESS, FAILURE, etc.)")
    old_data: Optional[Dict[str, Any]] = Field(None, description="Previous data state (for updates/deletes)")
    new_data: Optional[Dict[str, Any]] = Field(None, description="New data state (for creates/updates)")


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new AuditLog."""
    pass


class AuditLogInDB(AuditLogBase):
    """Schema for AuditLog stored in database."""
    id: int
    date: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLog(AuditLogInDB):
    """Schema for AuditLog response."""
    pass


class AuditLogWithUser(AuditLog):
    """Schema for AuditLog response with user details."""
    user: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogList(BaseModel):
    """Schema for paginated AuditLog list."""
    total: int
    items: list[AuditLog]
    
    model_config = ConfigDict(from_attributes=True)
