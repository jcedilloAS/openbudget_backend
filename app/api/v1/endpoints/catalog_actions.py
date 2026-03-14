from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.catalog_action import catalog_action
from app.schemas.catalog_action import (
    CatalogAction, 
    CatalogActionCreate, 
    CatalogActionUpdate, 
    CatalogActionList,
    CatalogActionListWithDetails
)
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=CatalogActionList, summary="List all catalog-actions")
def list_catalog_actions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    catalog_id: Optional[int] = Query(None, description="Filter by catalog ID"),
    action_id: Optional[int] = Query(None, description="Filter by action ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalog_actions", "read"))
):
    """
    Retrieve a list of catalog-actions with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **catalog_id**: Optional filter by catalog ID
    - **action_id**: Optional filter by action ID
    - **is_active**: Optional filter by active status
    """
    catalog_actions = catalog_action.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        catalog_id=catalog_id,
        action_id=action_id,
        is_active=is_active
    )
    total = catalog_action.count(db, catalog_id=catalog_id, action_id=action_id, is_active=is_active)
    
    return CatalogActionList(total=total, items=catalog_actions)


@router.get("/with-details", response_model=CatalogActionListWithDetails, summary="List catalog-actions with details")
def list_catalog_actions_with_details(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    catalog_id: Optional[int] = Query(None, description="Filter by catalog ID"),
    action_id: Optional[int] = Query(None, description="Filter by action ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalog_actions", "read"))
):
    """
    Retrieve a list of catalog-actions with catalog and action details.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **catalog_id**: Optional filter by catalog ID
    - **action_id**: Optional filter by action ID
    - **is_active**: Optional filter by active status
    """
    catalog_actions = catalog_action.get_multi_with_details(
        db, 
        skip=skip, 
        limit=limit, 
        catalog_id=catalog_id,
        action_id=action_id,
        is_active=is_active
    )
    total = catalog_action.count(db, catalog_id=catalog_id, action_id=action_id, is_active=is_active)
    
    return CatalogActionListWithDetails(total=total, items=catalog_actions)


@router.get("/{catalog_action_id}", response_model=CatalogAction, summary="Get catalog-action by ID")
def get_catalog_action(
    catalog_action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalog_actions", "read"))
):
    """
    Retrieve a specific catalog-action by ID.
    
    - **catalog_action_id**: The ID of the catalog-action to retrieve
    """
    db_catalog_action = catalog_action.get(db, catalog_action_id=catalog_action_id)
    
    if not db_catalog_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CatalogAction with id {catalog_action_id} not found"
        )
    
    return db_catalog_action


@router.post("/", response_model=CatalogAction, status_code=status.HTTP_201_CREATED, summary="Create new catalog-action")
def create_catalog_action(
    catalog_action_in: CatalogActionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalog_actions", "create"))
):
    """
    Create a new catalog-action relationship.
    
    - **catalog_id**: Catalog ID (required)
    - **action_id**: Action ID (required)
    - **is_active**: Whether the relationship is active (default: true)
    """
    ip_address = get_client_ip(request)
    return catalog_action.create(
        db, 
        catalog_action_in=catalog_action_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{catalog_action_id}", response_model=CatalogAction, summary="Update catalog-action")
def update_catalog_action(
    catalog_action_id: int,
    catalog_action_in: CatalogActionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalog_actions", "update"))
):
    """
    Update an existing catalog-action.
    
    - **catalog_action_id**: The ID of the catalog-action to update
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_catalog_action = catalog_action.update(
        db, 
        catalog_action_id=catalog_action_id, 
        catalog_action_in=catalog_action_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_catalog_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CatalogAction with id {catalog_action_id} not found"
        )
    
    return db_catalog_action


@router.delete("/{catalog_action_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete catalog-action")
def delete_catalog_action(
    catalog_action_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalog_actions", "delete"))
):
    """
    Delete a catalog-action.
    
    - **catalog_action_id**: The ID of the catalog-action to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_catalog_action = catalog_action.soft_delete(
            db, 
            catalog_action_id=catalog_action_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_catalog_action = catalog_action.delete(
            db, 
            catalog_action_id=catalog_action_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_catalog_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CatalogAction with id {catalog_action_id} not found"
        )
    
    return None
