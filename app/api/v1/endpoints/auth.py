from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    set_access_token_cookie,
    set_refresh_token_cookie,
    delete_access_token_cookie,
    delete_refresh_token_cookie,
    get_token_from_cookie,
    decode_token
)
from app.core.config import settings
from app.core.dependencies import get_current_user_from_cookie, get_current_user_with_permissions, get_user_permissions
from app.models.user import User
from app.crud.user import user as user_crud
from app.schemas.user import UserWithPermissions, PermissionItem

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseModel):
    """Login response schema."""
    message: str
    access_token: str
    refresh_token: str
    token_type: str
    user: dict
    permissions: list[PermissionItem]


class RefreshResponse(BaseModel):
    """Refresh token response schema."""
    message: str


class LogoutResponse(BaseModel):
    """Logout response schema."""
    message: str


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and set JWT tokens in cookies.
    
    - Accepts username or email
    - Returns user information
    - Sets access_token and refresh_token cookies
    """
    # Try to find user by username or email
    db_user = user_crud.get_by_username(db, username=login_data.username)
    if not db_user:
        db_user = user_crud.get_by_email(db, email=login_data.username)
    
    # Verify user exists and password is correct
    if not db_user or not verify_password(login_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access and refresh tokens
    access_token = create_access_token(data={"sub": db_user.id})
    refresh_token = create_refresh_token(data={"sub": db_user.id})
    
    # Set tokens in cookies
    set_access_token_cookie(response, access_token)
    set_refresh_token_cookie(response, refresh_token)
    
    # Update last login timestamp
    user_crud.update_last_login(db, user_id=db_user.id)
    
    permissions = get_user_permissions(db, db_user.role_id, is_superuser=bool(db_user.is_superuser))
    
    return LoginResponse(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": db_user.id,
            "username": db_user.username,
            "name": db_user.name,
            "email": db_user.email,
            "is_active": db_user.is_active,
            "role": {
                "id": db_user.role.id,
                "role_code": db_user.role.role_code,
                "name": db_user.role.name
            }
        },
        permissions=permissions
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from cookie.
    
    - Validates refresh token
    - Issues new access token
    - Optionally issues new refresh token (token rotation)
    """
    # Get refresh token from cookie
    refresh_token = get_token_from_cookie(request, settings.REFRESH_COOKIE_NAME)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate refresh token
    payload = decode_token(refresh_token)
    
    # Verify token type
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token (convert from string to int)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists and is active
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": user_id})
    set_access_token_cookie(response, new_access_token)
    
    # Optional: Rotate refresh token (recommended for security)
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    set_refresh_token_cookie(response, new_refresh_token)
    
    return RefreshResponse(message="Token refreshed successfully")


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response):
    """
    Logout user by clearing JWT tokens from cookies.
    
    - Deletes access_token and refresh_token cookies
    """
    delete_access_token_cookie(response)
    delete_refresh_token_cookie(response)
    
    return LogoutResponse(message="Logout successful")


@router.get("/me", response_model=UserWithPermissions)
def get_current_user_info(
    user_with_permissions: UserWithPermissions = Depends(get_current_user_with_permissions),
):
    """
    Get current authenticated user information with all available permissions.
    
    - Requires valid access token in cookie or Authorization header
    - Returns user details, role, and list of permissions
    """
    return user_with_permissions
