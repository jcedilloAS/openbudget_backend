from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.requisition import requisition
from app.schemas.requisition import (
    Requisition,
    RequisitionCreate,
    RequisitionUpdate,
    RequisitionList,
    RequisitionApprove,
    RequisitionReject,
    RequisitionWithDetails
)

router = APIRouter()


@router.get("/", response_model=RequisitionList, summary="List all requisitions")
def list_requisitions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    requested_by: Optional[int] = Query(None, description="Filter by requester user ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "list"))
):
    """
    Retrieve a list of requisitions with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **project_id**: Optional filter by project ID
    - **supplier_id**: Optional filter by supplier ID
    - **requested_by**: Optional filter by requester user ID
    - **status**: Optional filter by status
    - **created_by**: Optional filter by creator user ID
    """
    requisitions = requisition.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        project_id=project_id,
        supplier_id=supplier_id,
        requested_by=requested_by,
        status=status,
        created_by=created_by
    )
    total = requisition.count(
        db,
        project_id=project_id,
        supplier_id=supplier_id,
        requested_by=requested_by,
        status=status,
        created_by=created_by
    )
    
    return RequisitionList(total=total, items=requisitions)


@router.get("/search", response_model=RequisitionList, summary="Search requisitions")
def search_requisitions(
    q: str = Query(..., min_length=1, description="Search term (requisition number)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "list"))
):
    """
    Search requisitions by requisition number.
    
    - **q**: Search term
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    requisitions = requisition.search(db, search_term=q, skip=skip, limit=limit)
    return RequisitionList(total=len(requisitions), items=requisitions)


@router.get("/{requisition_id}", response_model=RequisitionWithDetails, summary="Get requisition by ID")
def get_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "list"))
):
    """
    Retrieve a specific requisition by ID.
    
    - **requisition_id**: The ID of the requisition to retrieve
    """
    db_requisition = requisition.get(db, requisition_id=requisition_id)
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return db_requisition


@router.get("/number/{requisition_number}", response_model=RequisitionWithDetails, summary="Get requisition by number")
def get_requisition_by_number(
    requisition_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "list"))
):
    """
    Retrieve a specific requisition by requisition number.
    
    - **requisition_number**: The unique number of the requisition to retrieve
    """
    db_requisition = requisition.get_by_requisition_number(db, requisition_number=requisition_number)
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with number '{requisition_number}' not found"
        )
    
    return db_requisition


@router.post("/", response_model=Requisition, status_code=status.HTTP_201_CREATED, summary="Create requisition")
def create_requisition(
    requisition_in: RequisitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "create"))
):
    """
    Create a new requisition.
    
    - **requisition_in**: Requisition data to create
    """
    return requisition.create(db, requisition_in=requisition_in, user_id=current_user.id)


@router.put("/{requisition_id}", response_model=Requisition, summary="Update requisition")
def update_requisition(
    requisition_id: int,
    requisition_in: RequisitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "update"))
):
    """
    Update an existing requisition.
    
    - **requisition_id**: The ID of the requisition to update
    - **requisition_in**: Updated requisition data
    """
    db_requisition = requisition.update(
        db, 
        requisition_id=requisition_id, 
        requisition_in=requisition_in,
        user_id=current_user.id
    )
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return db_requisition


@router.delete("/{requisition_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete requisition")
def delete_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "delete"))
):
    """
    Delete a requisition.
    
    - **requisition_id**: The ID of the requisition to delete
    """
    success = requisition.delete(db, requisition_id=requisition_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return None


@router.post("/{requisition_id}/submit", response_model=Requisition, summary="Submit requisition for approval")
def submit_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "submit"))
):
    """
    Submit a draft requisition for approval.
    Transitions status: draft → submitted.
    Adds total_amount to the project's commited balance.

    - **requisition_id**: The ID of the requisition to submit
    """
    db_requisition = requisition.submit(db, requisition_id=requisition_id, user_id=current_user.id)

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    return db_requisition


@router.post("/{requisition_id}/cancel", response_model=Requisition, summary="Cancel requisition")
def cancel_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "cancel"))
):
    """
    Cancel a draft or submitted requisition.
    Transitions status: draft/submitted → cancelled.
    If the requisition was submitted, releases the commited amount from the project.

    - **requisition_id**: The ID of the requisition to cancel
    """
    db_requisition = requisition.cancel(db, requisition_id=requisition_id, user_id=current_user.id)

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    return db_requisition


@router.post("/{requisition_id}/approve", response_model=Requisition, summary="Approve requisition")
def approve_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "approve"))
):
    """
    Approve a requisition.
    
    - **requisition_id**: The ID of the requisition to approve
    """
    db_requisition = requisition.approve(db, requisition_id=requisition_id, user_id=current_user.id)
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return db_requisition


@router.post("/{requisition_id}/reject", response_model=Requisition, summary="Reject requisition")
def reject_requisition(
    requisition_id: int,
    requisition_reject: RequisitionReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "reject"))
):
    """
    Reject a requisition.
    
    - **requisition_id**: The ID of the requisition to reject
    - **requisition_reject**: Rejection data including reason
    """
    db_requisition = requisition.reject(
        db, 
        requisition_id=requisition_id, 
        user_id=current_user.id,
        rejection_reason=requisition_reject.rejection_reason
    )
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return db_requisition
