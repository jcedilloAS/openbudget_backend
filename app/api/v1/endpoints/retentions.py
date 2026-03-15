from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.retention import retention
from app.schemas.retention import Retention, RetentionCreate, RetentionUpdate, RetentionList
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=RetentionList, summary="List all retentions")
def list_retentions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("retentions", "list"))
):
    """
    Retrieve a list of retentions with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    retentions = retention.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    total = retention.count(db, is_active=is_active)
    
    return RetentionList(total=total, items=retentions)


@router.get("/{retention_id}", response_model=Retention, summary="Get retention by ID")
def get_retention(
    retention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("retentions", "list"))
):
    """
    Retrieve a specific retention by ID.
    
    - **retention_id**: The ID of the retention to retrieve
    """
    db_retention = retention.get(db, retention_id=retention_id)
    
    if not db_retention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retention with id {retention_id} not found"
        )
    
    return db_retention


@router.post("/", response_model=Retention, status_code=status.HTTP_201_CREATED, summary="Create new retention")
def create_retention(
    retention_in: RetentionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("retentions", "create"))
):
    """
    Create a new retention.
    
    - **code**: Unique retention code (required)
    - **description**: Optional description of the retention
    - **percentage**: Retention percentage 0-100 (required)
    - **is_active**: Whether the retention is active (default: true)
    """
    ip_address = get_client_ip(request)
    return retention.create(
        db, 
        retention_in=retention_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{retention_id}", response_model=Retention, summary="Update retention")
def update_retention(
    retention_id: int,
    retention_in: RetentionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("retentions", "update"))
):
    """
    Update an existing retention.
    
    - **retention_id**: The ID of the retention to update
    - **code**: New retention code (optional)
    - **description**: New description (optional)
    - **percentage**: New percentage (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_retention = retention.update(
        db, 
        retention_id=retention_id, 
        retention_in=retention_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_retention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retention with id {retention_id} not found"
        )
    
    return db_retention


@router.delete("/{retention_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete retention")
def delete_retention(
    retention_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("retentions", "delete"))
):
    """
    Delete a retention.
    
    - **retention_id**: The ID of the retention to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_retention = retention.soft_delete(
            db, 
            retention_id=retention_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_retention = retention.delete(
            db, 
            retention_id=retention_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_retention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retention with id {retention_id} not found"
        )
    
    return None
