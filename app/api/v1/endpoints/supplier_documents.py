from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.supplier_document import supplier_document
from app.crud.supplier import supplier
from app.schemas.supplier_document import (
    SupplierDocument,
    SupplierDocumentCreate,
    SupplierDocumentUpdate,
    SupplierDocumentList,
)

router = APIRouter()


@router.get("/", response_model=SupplierDocumentList, summary="List documents for a supplier")
def list_supplier_documents(
    supplier_id: int = Query(..., gt=0, description="Supplier ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_documents", "list")),
):
    """
    Retrieve all documents for a specific supplier.

    - **supplier_id**: ID of the supplier
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    db_supplier = supplier.get(db, supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    documents = supplier_document.get_by_supplier(db, supplier_id=supplier_id, skip=skip, limit=limit)
    total = supplier_document.count_by_supplier(db, supplier_id=supplier_id)
    return SupplierDocumentList(total=total, items=documents)


@router.get("/{document_id}", response_model=SupplierDocument, summary="Get supplier document by ID")
def get_supplier_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_documents", "list")),
):
    """
    Retrieve a specific supplier document by ID.

    - **document_id**: The ID of the document to retrieve
    """
    db_document = supplier_document.get(db, document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier document with id {document_id} not found"
        )
    return db_document


@router.post("/", response_model=SupplierDocument, status_code=status.HTTP_201_CREATED, summary="Create supplier document")
def create_supplier_document(
    document_in: SupplierDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_documents", "create")),
):
    """
    Create a new document for a supplier.

    - **supplier_id**: Supplier ID (required)
    - **document_url**: URL of the document (required)
    - **description**: Optional description
    - **created_by**: User ID who created the document (required)
    - **updated_by**: User ID who last updated the document (required)
    """
    db_supplier = supplier.get(db, document_in.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {document_in.supplier_id} not found"
        )
    return supplier_document.create(db, document_in=document_in)


@router.put("/{document_id}", response_model=SupplierDocument, summary="Update supplier document")
def update_supplier_document(
    document_id: int,
    document_in: SupplierDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_documents", "update")),
):
    """
    Update an existing supplier document.

    - **document_id**: The ID of the document to update
    """
    db_document = supplier_document.update(db, document_id=document_id, document_in=document_in)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier document with id {document_id} not found"
        )
    return db_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete supplier document")
def delete_supplier_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("supplier_documents", "delete")),
):
    """
    Delete a supplier document.

    - **document_id**: The ID of the document to delete
    """
    db_document = supplier_document.delete(db, document_id=document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier document with id {document_id} not found"
        )
    return None
