from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.supplier import supplier
from app.schemas.supplier import (
    Supplier,
    SupplierCreate,
    SupplierUpdate,
    SupplierList,
    SupplierWithUsers
)

router = APIRouter()


@router.get("/", response_model=SupplierList, summary="List all suppliers")
def list_suppliers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "read"))
):
    """
    Retrieve a list of suppliers with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    - **created_by**: Optional filter by creator user ID
    """
    suppliers = supplier.get_multi(db, skip=skip, limit=limit, is_active=is_active, created_by=created_by)
    total = supplier.count(db, is_active=is_active, created_by=created_by)
    
    return SupplierList(total=total, items=suppliers)


@router.get("/search", response_model=SupplierList, summary="Search suppliers")
def search_suppliers(
    q: str = Query(..., min_length=1, description="Search term (name, code, or RFC)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "read"))
):
    """
    Search suppliers by name, supplier code, or RFC.
    
    - **q**: Search term
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    suppliers = supplier.search(db, search_term=q, skip=skip, limit=limit)
    return SupplierList(total=len(suppliers), items=suppliers)


@router.get("/{supplier_id}", response_model=SupplierWithUsers, summary="Get supplier by ID")
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "read"))
):
    """
    Retrieve a specific supplier by ID.
    
    - **supplier_id**: The ID of the supplier to retrieve
    """
    db_supplier = supplier.get(db, supplier_id=supplier_id)
    
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    return db_supplier


@router.get("/code/{supplier_code}", response_model=Supplier, summary="Get supplier by code")
def get_supplier_by_code(
    supplier_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "read"))
):
    """
    Retrieve a specific supplier by supplier code.
    
    - **supplier_code**: The unique code of the supplier to retrieve
    """
    db_supplier = supplier.get_by_supplier_code(db, supplier_code=supplier_code)
    
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with code '{supplier_code}' not found"
        )
    
    return db_supplier


@router.post("/", response_model=Supplier, status_code=status.HTTP_201_CREATED, summary="Create new supplier")
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "create"))
):
    """
    Create a new supplier.
    
    - **supplier_code**: Unique supplier code (required)
    - **name**: Supplier name (required)
    - **rfc**: RFC tax ID (optional)
    - **contact_name**: Contact person name (optional)
    - **contact_email**: Contact email (optional)
    - **contact_phone**: Contact phone (optional)
    - **address**: Physical address (optional)
    - **postal_code**: Postal code (optional)
    - **city**: City (optional)
    - **state**: State (optional)
    - **country**: Country (optional)
    - **percentage_iva**: IVA percentage (optional)
    - **delivery_time_days**: Delivery time in days (optional)
    - **is_active**: Active status (default: true)
    - **created_by**: User ID who created the supplier (required)
    - **updated_by**: User ID who last updated the supplier (required)
    """
    return supplier.create(db, supplier_in=supplier_in)


@router.put("/{supplier_id}", response_model=Supplier, summary="Update supplier")
def update_supplier(
    supplier_id: int,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "update"))
):
    """
    Update an existing supplier.
    
    - **supplier_id**: The ID of the supplier to update
    - All fields are optional for update
    """
    db_supplier = supplier.update(db, supplier_id=supplier_id, supplier_in=supplier_in)
    
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    return db_supplier


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete supplier")
def delete_supplier(
    supplier_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "delete"))
):
    """
    Delete a supplier.
    
    - **supplier_id**: The ID of the supplier to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    if soft:
        db_supplier = supplier.soft_delete(db, supplier_id=supplier_id)
    else:
        db_supplier = supplier.delete(db, supplier_id=supplier_id)
    
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    return None
