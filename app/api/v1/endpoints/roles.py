from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.crud.role import role
from app.schemas.role import Role, RoleCreate, RoleUpdate, RoleList, RoleWithPermissions
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=RoleList, summary="List all roles")
def list_roles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a list of roles with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    roles = role.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    total = role.count(db, is_active=is_active)
    
    return RoleList(total=total, items=roles)


@router.get("/{role_id}", response_model=Role, summary="Get role by ID")
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific role by ID.
    
    - **role_id**: The ID of the role to retrieve
    """
    db_role = role.get(db, role_id=role_id)
    
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )
    
    return db_role


@router.get("/{role_id}/with-permissions", response_model=RoleWithPermissions, summary="Get role with permissions")
def get_role_with_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific role by ID with its assigned permissions.
    
    - **role_id**: The ID of the role to retrieve
    """
    db_role = role.get_with_permissions(db, role_id=role_id)
    
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )
    
    return db_role


@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED, summary="Create new role")
def create_role(
    role_in: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new role.
    
    - **role_code**: Unique role code (required)
    - **name**: Role name (required)
    - **description**: Optional description of the role
    - **is_active**: Whether the role is active (default: true)
    """
    ip_address = get_client_ip(request)
    return role.create(
        db, 
        role_in=role_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{role_id}", response_model=Role, summary="Update role")
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing role.
    
    - **role_id**: The ID of the role to update
    - **role_code**: New role code (optional)
    - **name**: New name (optional)
    - **description**: New description (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_role = role.update(
        db, 
        role_id=role_id, 
        role_in=role_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )
    
    return db_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete role")
def delete_role(
    role_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a role.
    
    - **role_id**: The ID of the role to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_role = role.soft_delete(
            db, 
            role_id=role_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_role = role.delete(
            db, 
            role_id=role_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )
    
    return None
