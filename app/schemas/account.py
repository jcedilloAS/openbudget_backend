from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    """Base schema for Account."""
    account_number: str = Field(..., min_length=1, max_length=50, description="Account number")
    description: Optional[str] = Field(None, max_length=255, description="Account description")
    is_active: bool = Field(default=True, description="Whether the account is active")


class AccountCreate(AccountBase):
    """Schema for creating a new Account."""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an existing Account."""
    account_number: Optional[str] = Field(None, min_length=1, max_length=50, description="Account number")
    description: Optional[str] = Field(None, max_length=255, description="Account description")
    is_active: Optional[bool] = Field(None, description="Whether the account is active")


class AccountInDB(AccountBase):
    """Schema for Account stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Account(AccountInDB):
    """Schema for Account response."""
    pass


class AccountList(BaseModel):
    """Schema for paginated Account list."""
    total: int
    items: list[Account]
    
    model_config = ConfigDict(from_attributes=True)
