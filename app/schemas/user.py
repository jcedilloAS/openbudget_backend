from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.role import Role


class RoleSimple(BaseModel):
    """Simplified Role schema for nested responses."""
    id: int
    role_code: str
    name: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    """Base schema for User."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    role_id: int = Field(..., gt=0, description="Role ID for the user")
    is_active: bool = Field(default=True, description="Whether the user is active")


class UserCreate(BaseModel):
    """Schema for creating a new User."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=72, description="User's password (max 72 chars due to bcrypt limit)")
    role_id: int = Field(..., gt=0, description="Role ID for the user")
    is_active: bool = Field(default=True, description="Whether the user is active")


class UserUpdate(BaseModel):
    """Schema for updating an existing User."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(None, min_length=8, max_length=72, description="User's password (max 72 chars due to bcrypt limit)")
    role_id: Optional[int] = Field(None, gt=0, description="Role ID for the user")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")


class UserInDB(UserBase):
    """Schema for User stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Schema for User response."""
    pass


class UserWithRole(User):
    """Schema for User response with role details."""
    role: Optional[RoleSimple] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    """Schema for paginated User list."""
    total: int
    items: list[User]
    
    model_config = ConfigDict(from_attributes=True)
