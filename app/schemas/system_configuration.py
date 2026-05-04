from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class SystemConfigurationBase(BaseModel):
    """Base schema for SystemConfiguration."""
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    rfc: Optional[str] = Field(None, max_length=50, description="RFC (Tax ID)")
    smtp_host: Optional[str] = Field(None, max_length=255, description="SMTP server host")
    smtp_port: Optional[str] = Field(None, max_length=10, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, max_length=255, description="SMTP username")
    smtp_encryption: Optional[str] = Field(None, max_length=20, description="SMTP encryption type (TLS, SSL, None)")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo URL")
    requisition_serie: Optional[str] = Field(None, max_length=20, description="Requisition series prefix (e.g. REQ)")
    requisition_folio_next: Optional[int] = Field(None, ge=1, description="Next folio number to assign")


class SystemConfigurationCreate(SystemConfigurationBase):
    """Schema for creating a new SystemConfiguration."""
    smtp_password: Optional[str] = Field(None, max_length=255, description="SMTP password")


class SystemConfigurationUpdate(BaseModel):
    """Schema for updating an existing SystemConfiguration."""
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    rfc: Optional[str] = Field(None, max_length=50, description="RFC (Tax ID)")
    smtp_host: Optional[str] = Field(None, max_length=255, description="SMTP server host")
    smtp_port: Optional[str] = Field(None, max_length=10, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, max_length=255, description="SMTP username")
    smtp_password: Optional[str] = Field(None, max_length=255, description="SMTP password (omit if not changing)")
    smtp_encryption: Optional[str] = Field(None, max_length=20, description="SMTP encryption type (TLS, SSL, None)")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo URL")
    requisition_serie: Optional[str] = Field(None, max_length=20, description="Requisition series prefix (e.g. REQ)")
    requisition_folio_next: Optional[int] = Field(None, ge=1, description="Next folio number to assign")


class SystemConfigurationInDB(SystemConfigurationBase):
    """Schema for SystemConfiguration stored in database."""
    id: int
    created_at: datetime
    created_by: Optional[int] = None
    updated_at: datetime
    updated_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfiguration(SystemConfigurationInDB):
    """Schema for SystemConfiguration response (excludes sensitive data)."""
    pass


class SystemConfigurationWithPassword(SystemConfigurationInDB):
    """Schema for SystemConfiguration response including password (admin only)."""
    smtp_password: Optional[str] = Field(None, description="SMTP password (masked)")
    
    model_config = ConfigDict(from_attributes=True)
