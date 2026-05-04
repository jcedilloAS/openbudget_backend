import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.config import settings
from app.models.user import User
from app.crud.requisition_document import requisition_document
from app.crud.requisition import requisition
from app.schemas.requisition_document import (
    RequisitionDocument,
    RequisitionDocumentCreate,
    RequisitionDocumentUpdate,
    RequisitionDocumentList,
)
from app.utils.file_storage import save_uploaded_file, delete_file

router = APIRouter()


@router.get("/", response_model=RequisitionDocumentList, summary="List documents for a requisition")
def list_requisition_documents(
    requisition_id: int = Query(..., gt=0, description="Requisition ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_documents", "list")),
):
    db_requisition = requisition.get(db, requisition_id)
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    documents = requisition_document.get_by_requisition(db, requisition_id=requisition_id, skip=skip, limit=limit)
    total = requisition_document.count_by_requisition(db, requisition_id=requisition_id)
    return RequisitionDocumentList(total=total, items=documents)


@router.get("/{document_id}", response_model=RequisitionDocument, summary="Get requisition document by ID")
def get_requisition_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_documents", "list")),
):
    db_document = requisition_document.get(db, document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition document with id {document_id} not found"
        )
    return db_document


@router.post("/upload", response_model=RequisitionDocument, status_code=status.HTTP_201_CREATED, summary="Upload file and create requisition document")
async def upload_requisition_document(
    requisition_id: int = Query(..., gt=0, description="Requisition ID"),
    file: UploadFile = File(..., description="File to upload"),
    description: Optional[str] = Query(None, max_length=500, description="Document description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_documents", "create")),
):
    db_requisition = requisition.get(db, requisition_id)
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    file_url = await save_uploaded_file(
        file=file,
        subfolder="requisition_documents",
        upload_dir=settings.UPLOAD_DIR,
        max_size_mb=settings.MAX_UPLOAD_SIZE_MB
    )

    document_in = RequisitionDocumentCreate(
        requisition_id=requisition_id,
        description=description or file.filename,
        document_url=file_url,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    return requisition_document.create(db, document_in=document_in)


@router.post("/", response_model=RequisitionDocument, status_code=status.HTTP_201_CREATED, summary="Create requisition document")
def create_requisition_document(
    document_in: RequisitionDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_documents", "create")),
):
    db_req = requisition.get(db, document_in.requisition_id)
    if not db_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {document_in.requisition_id} not found"
        )
    return requisition_document.create(db, document_in=document_in)


@router.put("/{document_id}", response_model=RequisitionDocument, summary="Update requisition document")
def update_requisition_document(
    document_id: int,
    document_in: RequisitionDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_documents", "update")),
):
    db_document = requisition_document.update(db, document_id=document_id, document_in=document_in)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition document with id {document_id} not found"
        )
    return db_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete requisition document")
async def delete_requisition_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisition_documents", "delete")),
):
    db_document = requisition_document.get(db, document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition document with id {document_id} not found"
        )

    file_url = db_document.document_url
    requisition_document.delete(db, document_id=document_id)

    await delete_file(file_url=file_url, upload_dir=settings.UPLOAD_DIR)

    return None
