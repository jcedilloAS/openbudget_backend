from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.requisition_item import requisition_item
from app.schemas.requisition_item import (
    RequisitionItem,
    RequisitionItemCreate,
    RequisitionItemUpdate,
    RequisitionItemList
)

router = APIRouter()


@router.get("/", response_model=RequisitionItemList, summary="List all requisition items")
def list_requisition_items(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    requisition_id: Optional[int] = Query(None, description="Filter by requisition ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_items", "list"))
):
    """
    Retrieve a list of requisition items with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **requisition_id**: Optional filter by requisition ID
    """
    items = requisition_item.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        requisition_id=requisition_id
    )
    total = requisition_item.count(db, requisition_id=requisition_id)
    
    return RequisitionItemList(total=total, items=items)


@router.get("/{item_id}", response_model=RequisitionItem, summary="Get requisition item by ID")
def get_requisition_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_items", "list"))
):
    """
    Retrieve a specific requisition item by ID.
    
    - **item_id**: The ID of the requisition item to retrieve
    """
    db_item = requisition_item.get(db, item_id=item_id)
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition item with id {item_id} not found"
        )
    
    return db_item


@router.post("/", response_model=RequisitionItem, status_code=status.HTTP_201_CREATED, summary="Create requisition item")
def create_requisition_item(
    item_in: RequisitionItemCreate,
    requisition_id: int = Query(..., description="Requisition ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_items", "create"))
):
    """
    Create a new requisition item.
    
    - **item_in**: Requisition item data to create
    - **requisition_id**: The requisition ID this item belongs to
    """
    return requisition_item.create(db, item_in=item_in, requisition_id=requisition_id)


@router.put("/{item_id}", response_model=RequisitionItem, summary="Update requisition item")
def update_requisition_item(
    item_id: int,
    item_in: RequisitionItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_items", "update"))
):
    """
    Update an existing requisition item.
    
    - **item_id**: The ID of the requisition item to update
    - **item_in**: Updated requisition item data
    """
    db_item = requisition_item.update(db, item_id=item_id, item_in=item_in)
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition item with id {item_id} not found"
        )
    
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete requisition item")
def delete_requisition_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_items", "delete"))
):
    """
    Delete a requisition item.
    
    - **item_id**: The ID of the requisition item to delete
    """
    success = requisition_item.delete(db, item_id=item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition item with id {item_id} not found"
        )
    
    return None
