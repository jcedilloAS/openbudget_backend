from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.crud.account import account
from app.schemas.account import Account, AccountCreate, AccountUpdate, AccountList
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=AccountList, summary="List all accounts")
def list_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
