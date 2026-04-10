from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File
from sqlalchemy.orm import Session
from io import BytesIO
import openpyxl

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.account import account
from app.schemas.account import Account, AccountCreate, AccountUpdate, AccountList, AccountBulkUploadResult
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=AccountList, summary="List all accounts")
def list_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts", "list"))
):
    """
    Retrieve a list of accounts with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    accounts = account.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    total = account.count(db, is_active=is_active)
    
    return AccountList(total=total, items=accounts)


@router.get("/{account_id}", response_model=Account, summary="Get account by ID")
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts", "list"))
):
    """
    Retrieve a specific account by ID.
    
    - **account_id**: The ID of the account to retrieve
    """
    db_account = account.get(db, account_id=account_id)
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )
    
    return db_account


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED, summary="Create new account")
def create_account(
    account_in: AccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts", "create"))
):
    """
    Create a new account.
    
    - **account_number**: Unique account number (required)
    - **description**: Optional description of the account
    - **is_active**: Whether the account is active (default: true)
    """
    ip_address = get_client_ip(request)
    return account.create(
        db, 
        account_in=account_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{account_id}", response_model=Account, summary="Update account")
def update_account(
    account_id: int,
    account_in: AccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts", "update"))
):
    """
    Update an existing account.
    
    - **account_id**: The ID of the account to update
    - **account_number**: New account number (optional)
    - **description**: New description (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_account = account.update(
        db, 
        account_id=account_id, 
        account_in=account_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )
    
    return db_account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete account")
def delete_account(
    account_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts", "delete"))
):
    """
    Delete an account.
    
    - **account_id**: The ID of the account to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_account = account.soft_delete(
            db, 
            account_id=account_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_account = account.delete(
            db, 
            account_id=account_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with id {account_id} not found"
        )
    
    return None


@router.post("/bulk-upload", response_model=AccountBulkUploadResult, status_code=status.HTTP_200_OK, summary="Bulk upload accounts from Excel")
def bulk_upload_accounts(
    request: Request,
    file: UploadFile = File(..., description="Excel file (.xlsx). Col A = account_number, Col B = description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts", "create"))
):
    """
    Bulk create accounts from an Excel file (.xlsx).

    Row 1 is skipped (header). Data is read by position:
    - **Column A**: account_number
    - **Column B**: description (optional)

    Returns a summary with the number of created accounts, failed rows, and error details.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported"
        )

    content = file.file.read()

    try:
        wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file could not be read. Make sure it is a valid .xlsx file"
        )

    ws = wb.active
    all_rows = list(ws.iter_rows(min_row=2, values_only=True))  # skip header row

    if not all_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file is empty or only contains a header row"
        )

    data_rows = [row for row in all_rows if any(cell is not None for cell in row)]
    ip_address = get_client_ip(request)

    return account.bulk_create(db, rows=data_rows, current_user_id=current_user.id, ip_address=ip_address)
