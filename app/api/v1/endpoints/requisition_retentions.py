from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.requisition_retention import requisition_retention
from app.crud.requisition import requisition
from app.schemas.requisition_retention import (
    RequisitionRetention,
    RequisitionRetentionCreate,
    RequisitionRetentionUpdate,
    RequisitionRetentionList,
)

router = APIRouter()


@router.get("/", response_model=RequisitionRetentionList, summary="List retentions for a requisition")
def list_requisition_retentions(
    requisition_id: int = Query(..., gt=0, description="Requisition ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_retentions", "list")),
):
    db_req = requisition.get(db, requisition_id)
    if not db_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Requisition with id {requisition_id} not found")
    items = requisition_retention.get_by_requisition(db, requisition_id=requisition_id, skip=skip, limit=limit)
    total = requisition_retention.count_by_requisition(db, requisition_id=requisition_id)
    return RequisitionRetentionList(total=total, items=items)


@router.get("/{record_id}", response_model=RequisitionRetention, summary="Get requisition retention by ID")
def get_requisition_retention(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_retentions", "list")),
):
    db_record = requisition_retention.get(db, record_id)
    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Requisition retention with id {record_id} not found")
    return db_record


@router.post("/", response_model=RequisitionRetention, status_code=status.HTTP_201_CREATED, summary="Apply retention to requisition")
def create_requisition_retention(
    record_in: RequisitionRetentionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_retentions", "create")),
):
    db_req = requisition.get(db, record_in.requisition_id)
    if not db_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Requisition with id {record_in.requisition_id} not found")
    return requisition_retention.create(db, record_in=record_in, user_id=current_user.id)


@router.put("/{record_id}", response_model=RequisitionRetention, summary="Update retention amount on a requisition retention")
def update_requisition_retention(
    record_id: int,
    record_in: RequisitionRetentionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_retentions", "update")),
):
    db_record = requisition_retention.update(db, record_id=record_id, record_in=record_in, user_id=current_user.id)
    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Requisition retention with id {record_id} not found")
    return db_record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove retention from requisition")
def delete_requisition_retention(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_retentions", "delete")),
):
    success = requisition_retention.delete(db, record_id=record_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Requisition retention with id {record_id} not found")
    return None
