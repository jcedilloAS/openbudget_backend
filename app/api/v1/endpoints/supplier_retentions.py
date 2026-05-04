from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.supplier_retention import supplier_retention
from app.crud.supplier import supplier
from app.schemas.supplier_retention import (
    SupplierRetention,
    SupplierRetentionCreate,
    SupplierRetentionList,
)

router = APIRouter()


@router.get("/", response_model=SupplierRetentionList, summary="List retentions for a supplier")
def list_supplier_retentions(
    supplier_id: int = Query(..., gt=0, description="Supplier ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_retentions", "list")),
):
    db_supplier = supplier.get(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with id {supplier_id} not found")
    items = supplier_retention.get_by_supplier(db, supplier_id=supplier_id, skip=skip, limit=limit)
    total = supplier_retention.count_by_supplier(db, supplier_id=supplier_id)
    return SupplierRetentionList(total=total, items=items)


@router.get("/{record_id}", response_model=SupplierRetention, summary="Get supplier retention by ID")
def get_supplier_retention(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_retentions", "list")),
):
    db_record = supplier_retention.get(db, record_id)
    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier retention with id {record_id} not found")
    return db_record


@router.post("/", response_model=SupplierRetention, status_code=status.HTTP_201_CREATED, summary="Assign retention to supplier")
def create_supplier_retention(
    record_in: SupplierRetentionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_retentions", "create")),
):
    db_supplier = supplier.get(db, record_in.supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with id {record_in.supplier_id} not found")
    return supplier_retention.create(db, record_in=record_in, user_id=current_user.id)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove retention from supplier")
def delete_supplier_retention(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_retentions", "delete")),
):
    success = supplier_retention.delete(db, record_id=record_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier retention with id {record_id} not found")
    return None
