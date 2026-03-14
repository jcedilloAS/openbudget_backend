from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.core.database import get_db
from app.core.security import decode_token, get_token_from_cookie
from app.core.config import settings
from app.models.user import User
from app.models.role_permission import RolePermission
from app.models.catalog_action import CatalogAction
from app.models.catalog import Catalog
from app.models.action import Action
from app.schemas.user import PermissionItem, UserWithPermissions

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


def get_user_permissions(db: Session, role_id: int, is_superuser: bool = False) -> List[PermissionItem]:
    """
    Get all permissions for a given role.
    Superusers get all active catalog_actions regardless of role_permissions.
    
    Args:
        db: Database session
        role_id: Role ID to get permissions for
        is_superuser: Whether the user is a superuser
        
    Returns:
        List of PermissionItem with catalog_code, catalog_name, action_code, action_name
    """
    query = (
        db.query(
            Catalog.catalog_code,
            Catalog.catalog_name,
            Action.action_code,
            Action.action_name,
        )
        .join(CatalogAction, CatalogAction.catalog_id == Catalog.id)
        .join(Action, CatalogAction.action_id == Action.id)
    )

    if is_superuser:
        query = query.filter(CatalogAction.is_active == True)
    else:
        query = (
            query
            .join(RolePermission, RolePermission.catalog_action_id == CatalogAction.id)
            .filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.is_allowed == True,
                    CatalogAction.is_active == True,
                )
            )
        )

    results = query.all()
    return [
        PermissionItem(
            catalog_code=r.catalog_code,
            catalog_name=r.catalog_name,
            action_code=r.action_code,
            action_name=r.action_name,
        )
        for r in results
    ]


def get_current_user_with_permissions(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserWithPermissions:
    """
    Get the current authenticated user together with all their permissions.

    Returns:
        UserWithPermissions schema with role and permission list
    """
    user = get_current_user_from_cookie(request, db, credentials)
    permissions = get_user_permissions(db, user.role_id, is_superuser=bool(user.is_superuser))

    return UserWithPermissions(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        role_id=user.role_id,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        role={
            "id": user.role.id,
            "role_code": user.role.role_code,
            "name": user.role.name,
            "description": user.role.description,
        } if user.role else None,
        permissions=permissions,
    )


def require_permission(catalog_code: str, action_code: str):
    """
    Dependency factory to validate that the current user's role has a specific
    permission (catalog_code + action_code).

    Usage:
        @router.get("/", dependencies=[Depends(require_permission("accounts", "read"))])
        def list_accounts(...):
            ...

    Or inject the user:
        current_user: User = Depends(require_permission("accounts", "read"))

    Args:
        catalog_code: The catalog code (e.g. "accounts", "users", "roles")
        action_code: The action code (e.g. "create", "read", "update", "delete")

    Returns:
        Dependency function that returns the current active User
    """
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Query for the specific permission
        permission = (
            db.query(RolePermission)
            .join(CatalogAction, RolePermission.catalog_action_id == CatalogAction.id)
            .join(Catalog, CatalogAction.catalog_id == Catalog.id)
            .join(Action, CatalogAction.action_id == Action.id)
            .filter(
                and_(
                    RolePermission.role_id == current_user.role_id,
                    Catalog.catalog_code == catalog_code,
                    Action.action_code == action_code,
                    RolePermission.is_allowed == True,
                    CatalogAction.is_active == True,
                )
            )
            .first()
        )

        if not permission and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {catalog_code}:{action_code}",
            )

        return current_user

    return permission_checker
