from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.crud.role_permission import role_permission
from app.schemas.role_permission import (
    RolePermission, 
    RolePermissionCreate, 
    RolePermissionUpdate, 
    RolePermissionList,
    RolePermissionListWithDetails,
    RolePermissionBulkCreate
)
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=RolePermissionList, summary="List all role permissions")
def list_role_permissions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    catalog_action_id: Optional[int] = Query(None, description="Filter by catalog-action ID"),
    is_allowed: Optional[bool] = Query(None, description="Filter by allowed status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a list of role permissions with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **role_id**: Optional filter by role ID
    - **catalog_action_id**: Optional filter by catalog-action ID
    - **is_allowed**: Optional filter by allowed status
    """
    role_permissions = role_permission.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        role_id=role_id,
        catalog_action_id=catalog_action_id,
        is_allowed=is_allowed
    )
    total = role_permission.count(db, role_id=role_id, catalog_action_id=catalog_action_id, is_allowed=is_allowed)
    
    return RolePermissionList(total=total, items=role_permissions)


@router.get("/with-details", response_model=RolePermissionListWithDetails, summary="List role permissions with details")
def list_role_permissions_with_details(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    catalog_action_id: Optional[int] = Query(None, description="Filter by catalog-action ID"),
    is_allowed: Optional[bool] = Query(None, description="Filter by allowed status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a list of role permissions with role, catalog and action details.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **role_id**: Optional filter by role ID
    - **catalog_action_id**: Optional filter by catalog-action ID
    - **is_allowed**: Optional filter by allowed status
    """
    role_permissions = role_permission.get_multi_with_details(
        db, 
        skip=skip, 
        limit=limit, 
        role_id=role_id,
        catalog_action_id=catalog_action_id,
        is_allowed=is_allowed
    )
    total = role_permission.count(db, role_id=role_id, catalog_action_id=catalog_action_id, is_allowed=is_allowed)
    
    return RolePermissionListWithDetails(total=total, items=role_permissions)


@router.get("/{role_permission_id}", response_model=RolePermission, summary="Get role permission by ID")
def get_role_permission(
    role_permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific role permission by ID.
    
    - **role_permission_id**: The ID of the role permission to retrieve
    """
    db_role_permission = role_permission.get(db, role_permission_id=role_permission_id)
    
    if not db_role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RolePermission with id {role_permission_id} not found"
        )
    
    return db_role_permission


@router.post("/", response_model=RolePermission, status_code=status.HTTP_201_CREATED, summary="Create new role permission")
def create_role_permission(
    role_permission_in: RolePermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new role permission.
    
    - **role_id**: Role ID (required)
    - **catalog_action_id**: Catalog-Action ID (required)
    - **is_allowed**: Whether the permission is allowed or denied (default: true)
    """
    ip_address = get_client_ip(request)
    return role_permission.create(
        db, 
        role_permission_in=role_permission_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.post("/bulk", response_model=List[RolePermission], status_code=status.HTTP_201_CREATED, summary="Bulk create role permissions")
def bulk_create_role_permissions(
    bulk_data: RolePermissionBulkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk create role permissions for a role.
    
    - **role_id**: Role ID (required)
    - **catalog_action_ids**: List of Catalog-Action IDs (required)
    - **is_allowed**: Whether the permissions are allowed or denied (default: true)
    """
    ip_address = get_client_ip(request)
    return role_permission.bulk_create(
        db,
        bulk_data=bulk_data,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{role_permission_id}", response_model=RolePermission, summary="Update role permission")
def update_role_permission(
    role_permission_id: int,
    role_permission_in: RolePermissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing role permission.
    
    - **role_permission_id**: The ID of the role permission to update
    - **is_allowed**: New allowed status (optional)
    """
    ip_address = get_client_ip(request)
    db_role_permission = role_permission.update(
        db, 
        role_permission_id=role_permission_id, 
        role_permission_in=role_permission_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RolePermission with id {role_permission_id} not found"
        )
    
    return db_role_permission


@router.delete("/{role_permission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete role permission")
def delete_role_permission(
    role_permission_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a role permission.
    
    - **role_permission_id**: The ID of the role permission to delete
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    db_role_permission = role_permission.delete(
        db, 
        role_permission_id=role_permission_id,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RolePermission with id {role_permission_id} not found"
        )
    
    return None
