from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User as UserModel
from app.crud.user import user
from app.schemas.user import User, UserCreate, UserUpdate, UserList, UserWithRole
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=UserList, summary="List all users")
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "read"))
):
    """
    Retrieve a list of users with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    - **role_id**: Optional filter by role ID
    """
    users = user.get_multi(db, skip=skip, limit=limit, is_active=is_active, role_id=role_id)
    total = user.count(db, is_active=is_active, role_id=role_id)
    
    return UserList(total=total, items=users)


@router.get("/{user_id}", response_model=UserWithRole, summary="Get user by ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "read"))
):
    """
    Retrieve a specific user by ID.
    
    - **user_id**: The ID of the user to retrieve
    """
    db_user = user.get(db, user_id=user_id)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return db_user


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED, summary="Create new user")
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "create"))
):
    """
    Create a new user.
    
    - **username**: Unique username (required, min 3 chars)
    - **name**: User's full name (required)
    - **email**: Valid email address (required)
    - **password**: Password (required, min 8 chars)
    - **role_id**: Role ID for the user (required)
    - **is_active**: Whether the user is active (default: true)
    """
    ip_address = get_client_ip(request)
    return user.create(
        db, 
        user_in=user_in, 
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{user_id}", response_model=User, summary="Update user")
def update_user(
    user_id: int,
    user_in: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "update"))
):
    """
    Update an existing user.
    
    - **user_id**: The ID of the user to update
    - **username**: New username (optional)
    - **name**: New name (optional)
    - **email**: New email (optional)
    - **password**: New password (optional)
    - **role_id**: New role ID (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_user = user.update(
        db, 
        user_id=user_id, 
        user_in=user_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
def delete_user(
    user_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "delete"))
):
    """
    Delete a user.
    
    - **user_id**: The ID of the user to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_user = user.soft_delete(
            db, 
            user_id=user_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_user = user.delete(
            db, 
            user_id=user_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return None


@router.get("/username/{username}", response_model=User, summary="Get user by username")
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "read"))
):
    """
    Retrieve a specific user by username.
    
    - **username**: The username of the user to retrieve
    """
    db_user = user.get_by_username(db, username=username)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found"
        )
    
    return db_user


@router.get("/email/{email}", response_model=User, summary="Get user by email")
def get_user_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission("users", "read"))
):
    """
    Retrieve a specific user by email.
    
    - **email**: The email of the user to retrieve
    """
    db_user = user.get_by_email(db, email=email)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    
    return db_user
