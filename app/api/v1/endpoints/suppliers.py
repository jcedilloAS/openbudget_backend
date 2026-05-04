from typing import List, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.config import settings
from app.models.user import User
from app.crud.supplier import supplier
from app.schemas.supplier import (
    Supplier,
    SupplierCreate,
    SupplierUpdate,
    SupplierList,
    SupplierWithUsers,
    SupplierWithDocuments
)
from app.schemas.supplier_document import SupplierDocumentInline
from app.utils.file_storage import save_uploaded_file

router = APIRouter()


@router.get("/", response_model=SupplierList, summary="List all suppliers")
def list_suppliers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "list"))
):
    """
    Retrieve a list of suppliers with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    - **created_by**: Optional filter by creator user ID
    - **category_id**: Optional filter by category ID
    """
    suppliers_list = supplier.get_multi(db, skip=skip, limit=limit, is_active=is_active, created_by=created_by, category_id=category_id)
    total = supplier.count(db, is_active=is_active, created_by=created_by, category_id=category_id)
    
    # Add category_name to each supplier from the loaded relationship
    items = []
    for s in suppliers_list:
        supplier_data = Supplier.model_validate(s)
        if hasattr(s, 'category') and s.category:
            supplier_data.category_name = s.category.name
        items.append(supplier_data)
    
    return SupplierList(total=total, items=items)


@router.get("/search", response_model=SupplierList, summary="Search suppliers")
def search_suppliers(
    q: str = Query(..., min_length=1, description="Search term (name, code, or RFC)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "list"))
):
    """
    Search suppliers by name, supplier code, or RFC.
    
    - **q**: Search term
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    suppliers_list = supplier.search(db, search_term=q, skip=skip, limit=limit)
    
    # Add category_name to each supplier from the loaded relationship
    items = []
    for s in suppliers_list:
        supplier_data = Supplier.model_validate(s)
        if hasattr(s, 'category') and s.category:
            supplier_data.category_name = s.category.name
        items.append(supplier_data)
    
    return SupplierList(total=len(suppliers_list), items=items)


@router.get("/{supplier_id}", response_model=SupplierWithDocuments, summary="Get supplier by ID")
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "list"))
):
    """
    Retrieve a specific supplier by ID, including its documents.
    
    - **supplier_id**: The ID of the supplier to retrieve
    """
    db_supplier = supplier.get(db, supplier_id=supplier_id)
    
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    # Add category_name from the loaded relationship
    supplier_data = SupplierWithDocuments.model_validate(db_supplier)
    if hasattr(db_supplier, 'category') and db_supplier.category:
        supplier_data.category_name = db_supplier.category.name
    
    return supplier_data


@router.get("/code/{supplier_code}", response_model=SupplierWithDocuments, summary="Get supplier by code")
def get_supplier_by_code(
    supplier_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "list"))
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
    
    # Add category_name from the loaded relationship
    supplier_data = SupplierWithDocuments.model_validate(db_supplier)
    if hasattr(db_supplier, 'category') and db_supplier.category:
        supplier_data.category_name = db_supplier.category.name
    
    return supplier_data


@router.post("/", response_model=SupplierWithDocuments, status_code=status.HTTP_201_CREATED, summary="Create new supplier")
async def create_supplier(
    supplier_data: str = Form(..., description="JSON string with supplier data"),
    files: List[UploadFile] = File(default=[], description="Document files to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "create"))
):
    """
    Create a new supplier with optional document uploads.
    
    **Multipart form fields:**
    - **supplier_data**: JSON string containing supplier information:
      - supplier_code: Unique supplier code (required)
      - name: Supplier name (required)
      - rfc: RFC tax ID (optional)
      - phone: Phone number (optional)
      - address: Physical address (optional)
      - postal_code: Postal code (optional)
      - city: City (optional)
      - state: State (optional)
      - country: Country (optional)
      - percentage_iva: IVA percentage (optional)
      - delivery_time_days: Delivery time in days (optional)
      - is_active: Active status (default: true)
    - **files**: Multiple files (PDF, images, DOCX, XLSX) up to 10MB each
    """
    # Parse supplier data from JSON string
    try:
        supplier_in = SupplierCreate.model_validate_json(supplier_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid supplier data: {str(e)}"
        )
    
    # Save uploaded files and build documents list
    documents = []
    for file in files:
        try:
            file_url = await save_uploaded_file(
                file=file,
                subfolder="supplier_documents",
                upload_dir=settings.UPLOAD_DIR,
                max_size_mb=settings.MAX_UPLOAD_SIZE_MB
            )
            documents.append(SupplierDocumentInline(
                description=file.filename,
                document_url=file_url
            ))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file {file.filename}: {str(e)}"
            )
    
    # Add documents to supplier data
    if documents:
        supplier_in.documents = documents
    
    db_supplier = supplier.create(db, supplier_in=supplier_in, user_id=current_user.id)
    
    # Reload with category relationship
    db.refresh(db_supplier)
    db_supplier = supplier.get(db, supplier_id=db_supplier.id)
    
    # Add category_name from the loaded relationship
    supplier_data_response = SupplierWithDocuments.model_validate(db_supplier)
    if hasattr(db_supplier, 'category') and db_supplier.category:
        supplier_data_response.category_name = db_supplier.category.name
    
    return supplier_data_response


@router.put("/{supplier_id}", response_model=SupplierWithDocuments, summary="Update supplier")
async def update_supplier(
    supplier_id: int,
    supplier_data: str = Form(..., description="JSON string with supplier data"),
    files: List[UploadFile] = File(default=[], description="New document files to upload"),
    existing_documents: Optional[str] = Form(None, description="JSON array of existing documents to keep"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("suppliers", "update"))
):
    """
    Update an existing supplier with optional document uploads.
    
    **Multipart form fields:**
    - **supplier_data**: JSON string with fields to update (all optional)
    - **files**: New files to upload (optional)
    - **existing_documents**: JSON array of existing documents to keep, e.g.:
      `[{"id": 1, "description": "Contract", "document_url": "/uploads/..."}]`
      Documents not in this array will be deleted.
      Omit this field to keep all existing documents unchanged.
    """
    # Parse supplier data from JSON string
    try:
        supplier_in = SupplierUpdate.model_validate_json(supplier_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid supplier data: {str(e)}"
        )
    
    # Check if supplier exists first (needed if we have new files but no existing_documents)
    db_supplier_check = supplier.get(db, supplier_id=supplier_id)
    if not db_supplier_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    # Parse existing documents if provided
    documents = []
    if existing_documents:
        try:
            existing_docs_data = json.loads(existing_documents)
            documents = [SupplierDocumentInline(**doc) for doc in existing_docs_data]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid existing_documents data: {str(e)}"
            )
    elif files:
        # If no existing_documents provided but files are being uploaded,
        # we need to preserve existing documents and add new ones
        for existing_doc in db_supplier_check.documents:
            documents.append(SupplierDocumentInline(
                id=existing_doc.id,
                description=existing_doc.description,
                document_url=existing_doc.document_url
            ))
    
    # Save new uploaded files
    for file in files:
        try:
            file_url = await save_uploaded_file(
                file=file,
                subfolder="supplier_documents",
                upload_dir=settings.UPLOAD_DIR,
                max_size_mb=settings.MAX_UPLOAD_SIZE_MB
            )
            documents.append(SupplierDocumentInline(
                description=file.filename,
                document_url=file_url
            ))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file {file.filename}: {str(e)}"
            )
    
    # Set documents if any were provided (existing or new)
    # If existing_documents was provided (even as empty array), it means we want to sync documents
    # If existing_documents was not provided (None) and no files, we don't touch documents
    if existing_documents is not None or files:
        supplier_in.documents = documents
    
    db_supplier = supplier.update(db, supplier_id=supplier_id, supplier_in=supplier_in, user_id=current_user.id)
    
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    # Reload with category relationship
    db.refresh(db_supplier)
    db_supplier = supplier.get(db, supplier_id=db_supplier.id)
    
    # Add category_name from the loaded relationship
    supplier_data_response = SupplierWithDocuments.model_validate(db_supplier)
    if hasattr(db_supplier, 'category') and db_supplier.category:
        supplier_data_response.category_name = db_supplier.category.name
    
    return supplier_data_response


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
