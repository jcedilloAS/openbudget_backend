import json
from io import BytesIO
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, status, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.config import settings
from app.models.user import User
from app.crud.requisition import requisition
from app.utils.request import get_client_ip
from app.utils.file_storage import save_uploaded_file
from app.schemas.requisition import (
    Requisition,
    RequisitionCreate,
    RequisitionUpdate,
    RequisitionList,
    RequisitionApprove,
    RequisitionReject,
    RequisitionWithDetails,
    RequisitionWithDocuments
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


@router.get("/{requisition_id}/pdf", summary="Generate PDF for a requisition")
def get_requisition_pdf(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "list"))
):
    """
    Generate and return a PDF document for the specified requisition.
    Returns the PDF inline so it can be embedded directly in an iframe.

    - **requisition_id**: The ID of the requisition
    """
    from app.models.requisition import Requisition as RequisitionModel
    from app.models.requisition_item import RequisitionItem as RequisitionItemModel
    from app.models.requisition_retention import RequisitionRetention as RequisitionRetentionModel
    from app.utils.pdf_generator import generate_requisition_pdf
    from app.crud.system_configuration import system_configuration as sys_config_crud

    db_requisition = (
        db.query(RequisitionModel)
        .options(
            joinedload(RequisitionModel.project),
            joinedload(RequisitionModel.supplier),
            joinedload(RequisitionModel.requester),
            joinedload(RequisitionModel.approver),
            joinedload(RequisitionModel.rejector),
            joinedload(RequisitionModel.retentions).joinedload(RequisitionRetentionModel.retention),
            joinedload(RequisitionModel.items).joinedload(RequisitionItemModel.account),
        )
        .filter(RequisitionModel.id == requisition_id)
        .first()
    )

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    sys_config = sys_config_crud.get_active(db)
    pdf_bytes = generate_requisition_pdf(db_requisition, sys_config)
    filename = f"requisicion-{db_requisition.requisition_number}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/{requisition_id}", response_model=RequisitionWithDocuments, summary="Get requisition by ID")
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


@router.post("/", response_model=RequisitionWithDocuments, status_code=status.HTTP_201_CREATED, summary="Create requisition")
async def create_requisition(
    request: Request,
    requisition_data: str = Form(..., description="JSON string with requisition data"),
    files: List[UploadFile] = File(default=[], description="Document files to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "create"))
):
    """
    Create a new requisition with optional document uploads.

    **Multipart form fields:**
    - **requisition_data**: JSON string with requisition data (same fields as before, including `items` and `documents`)
    - **files**: Files to upload; matched by index to entries in `documents` that have no `document_url`
    """
    from app.schemas.requisition_document import RequisitionDocumentInline

    try:
        requisition_in = RequisitionCreate.model_validate_json(requisition_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid requisition data: {e}")

    # Upload files and assign URLs to documents that don't have one yet
    if files:
        documents = list(requisition_in.documents or [])
        file_index = 0
        for i, doc in enumerate(documents):
            if not doc.document_url and file_index < len(files):
                file = files[file_index]
                file_index += 1
                try:
                    file_url = await save_uploaded_file(
                        file=file,
                        subfolder="requisition_documents",
                        upload_dir=settings.UPLOAD_DIR,
                        max_size_mb=settings.MAX_UPLOAD_SIZE_MB
                    )
                    documents[i] = RequisitionDocumentInline(
                        description=doc.description or file.filename,
                        document_url=file_url
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process file {file.filename}: {e}")
        # Also append any extra files not tied to a documents entry
        while file_index < len(files):
            file = files[file_index]
            file_index += 1
            file_url = await save_uploaded_file(
                file=file,
                subfolder="requisition_documents",
                upload_dir=settings.UPLOAD_DIR,
                max_size_mb=settings.MAX_UPLOAD_SIZE_MB
            )
            documents.append(RequisitionDocumentInline(description=file.filename, document_url=file_url))
        requisition_in.documents = documents

    db_requisition = requisition.create(db, requisition_in=requisition_in, user_id=current_user.id, ip_address=get_client_ip(request))
    db.refresh(db_requisition)
    db_requisition = requisition.get(db, db_requisition.id)
    return RequisitionWithDocuments.model_validate(db_requisition)


@router.put("/{requisition_id}", response_model=RequisitionWithDocuments, summary="Update requisition")
async def update_requisition(
    request: Request,
    requisition_id: int,
    requisition_data: str = Form(..., description="JSON string with requisition data"),
    files: List[UploadFile] = File(default=[], description="New document files to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "update"))
):
    """
    Update an existing requisition.

    **Multipart form fields:**
    - **requisition_data**: JSON string with requisition data (same fields as RequisitionUpdate, including `items`, `documents`, `retentions`)
    - **files**: New files to upload; matched by index to `documents` entries that have no `document_url`
    """
    from app.schemas.requisition_document import RequisitionDocumentInline

    try:
        requisition_in = RequisitionUpdate.model_validate_json(requisition_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid requisition data: {e}")

    if files:
        documents = list(requisition_in.documents or [])
        file_index = 0
        for i, doc in enumerate(documents):
            if not doc.document_url and file_index < len(files):
                file = files[file_index]
                file_index += 1
                try:
                    file_url = await save_uploaded_file(
                        file=file,
                        subfolder="requisition_documents",
                        upload_dir=settings.UPLOAD_DIR,
                        max_size_mb=settings.MAX_UPLOAD_SIZE_MB
                    )
                    documents[i] = RequisitionDocumentInline(
                        description=doc.description or file.filename,
                        document_url=file_url
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process file {file.filename}: {e}")
        while file_index < len(files):
            file = files[file_index]
            file_index += 1
            file_url = await save_uploaded_file(
                file=file,
                subfolder="requisition_documents",
                upload_dir=settings.UPLOAD_DIR,
                max_size_mb=settings.MAX_UPLOAD_SIZE_MB
            )
            documents.append(RequisitionDocumentInline(description=file.filename, document_url=file_url))
        requisition_in.documents = documents

    db_requisition = requisition.update(
        db,
        requisition_id=requisition_id,
        requisition_in=requisition_in,
        user_id=current_user.id,
        ip_address=get_client_ip(request)
    )

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    db.refresh(db_requisition)
    db_requisition = requisition.get(db, db_requisition.id)
    return RequisitionWithDocuments.model_validate(db_requisition)


@router.delete("/{requisition_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete requisition")
def delete_requisition(
    request: Request,
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "delete"))
):
    """
    Delete a requisition.

    - **requisition_id**: The ID of the requisition to delete
    """
    success = requisition.delete(db, requisition_id=requisition_id, user_id=current_user.id, ip_address=get_client_ip(request))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return None


@router.post("/{requisition_id}/submit", response_model=Requisition, summary="Submit requisition for approval")
def submit_requisition(
    request: Request,
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
    db_requisition = requisition.submit(db, requisition_id=requisition_id, user_id=current_user.id, ip_address=get_client_ip(request))

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    return db_requisition


@router.post("/{requisition_id}/cancel", response_model=Requisition, summary="Cancel requisition")
def cancel_requisition(
    request: Request,
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
    db_requisition = requisition.cancel(db, requisition_id=requisition_id, user_id=current_user.id, ip_address=get_client_ip(request))

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    return db_requisition


@router.post("/{requisition_id}/approve", response_model=Requisition, summary="Approve requisition")
def approve_requisition(
    request: Request,
    requisition_id: int,
    approve_data: RequisitionApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "approve"))
):
    """
    Approve a requisition.

    - **requisition_id**: The ID of the requisition to approve
    - **approve_data**: Approval data including optional retention_id
    """
    db_requisition = requisition.approve(
        db,
        requisition_id=requisition_id,
        user_id=current_user.id,
        item_account_assignments=approve_data.item_account_assignments,
        ip_address=get_client_ip(request)
    )
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return db_requisition


@router.post("/{requisition_id}/reject", response_model=Requisition, summary="Reject requisition")
def reject_requisition(
    request: Request,
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
        rejection_reason=requisition_reject.rejection_reason,
        ip_address=get_client_ip(request)
    )
    
    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )
    
    return db_requisition


#@router.post("/{requisition_id}/revert-to-draft", response_model=RequisitionWithDetails, summary="Revert requisition to draft")
def revert_requisition_to_draft(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("requisitions", "revert_to_draft"))
):
    """
    Revert a submitted requisition back to draft so it can be edited before approval.
    Transitions status: submitted → draft.
    Releases the committed amount from the project budget.

    - **requisition_id**: The ID of the requisition to revert
    """
    db_requisition = requisition.revert_to_draft(db, requisition_id=requisition_id, user_id=current_user.id)

    if not db_requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition with id {requisition_id} not found"
        )

    return db_requisition
