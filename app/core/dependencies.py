from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import decode_token, get_token_from_cookie
from app.core.config import settings
from app.models.user import User

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Get JWT token from cookie or Authorization header.
    
    Priority:
    1. Authorization header (Bearer token)
    2. Cookie
    
    Args:
        request: FastAPI Request object
        credentials: Optional Bearer token from Authorization header
        
    Returns:
        JWT token string or None
    """
    # Try to get token from Authorization header first
    if credentials and credentials.scheme == "Bearer":
        return credentials.credentials
    
    # Fallback to cookie
    return get_token_from_cookie(request, settings.COOKIE_NAME)


def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current user from JWT token in cookie or Authorization header.
    
    Args:
        request: FastAPI Request object
        db: Database session
        credentials: Optional Bearer token from Authorization header
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get token from Authorization header or cookie
    token = get_token_from_request(request, credentials)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    
    # Verify token type
    token_type = payload.get("type")
    if token_type != "access":
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
    
    # Get user from database with role eager loaded
    user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user_from_cookie)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: User from get_current_user_from_cookie dependency
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user from cookie or header, but return None if not authenticated.
    Useful for endpoints that work with or without authentication.
    
    Args:
        request: FastAPI Request object
        db: Database session
        credentials: Optional Bearer token from Authorization header
        
    Returns:
        Current user or None
    """
    try:
        return get_current_user_from_cookie(request, db, credentials)
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Dependency factory to check if user has required role.
    
    Args:
        required_role: Role code required to access the endpoint
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.role_code != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return current_user
    
    return role_checker
