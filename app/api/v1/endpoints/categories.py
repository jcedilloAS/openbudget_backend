from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.category import category
from app.schemas.category import Category, CategoryCreate, CategoryUpdate, CategoryList
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=CategoryList, summary="List all categories")
def list_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("categories", "list"))
):
    """
    Retrieve a list of categories with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    categories = category.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    total = category.count(db, is_active=is_active)
    
    return CategoryList(total=total, items=categories)


@router.get("/{category_id}", response_model=Category, summary="Get category by ID")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("categories", "list"))
):
    """
    Retrieve a specific category by ID.
    
    - **category_id**: The ID of the category to retrieve
    """
    db_category = category.get(db, category_id=category_id)
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    return db_category


@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED, summary="Create new category")
def create_category(
    category_in: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("categories", "create"))
):
    """
    Create a new category.
    
    - **name**: Category name (required)
    - **description**: Optional description of the category
    - **is_active**: Whether the category is active (default: true)
    """
    ip_address = get_client_ip(request)
    return category.create(
        db, 
        category_in=category_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{category_id}", response_model=Category, summary="Update category")
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("categories", "update"))
):
    """
    Update an existing category.
    
    - **category_id**: The ID of the category to update
    - **name**: New category name (optional)
    - **description**: New description (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_category = category.update(
        db, 
        category_id=category_id, 
        category_in=category_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete category")
def delete_category(
    category_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("categories", "delete"))
):
    """
    Delete a category.
    
    - **category_id**: The ID of the category to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    
    Note: Categories in use by suppliers cannot be deleted.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_category = category.soft_delete(
            db, 
            category_id=category_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_category = category.delete(
            db, 
            category_id=category_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    return None


@router.get("/search/", response_model=CategoryList, summary="Search categories")
def search_categories(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("categories", "list"))
):
    """
    Search categories by name or description.
    
    - **q**: Search term (required)
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    categories = category.search(db, search_term=q, skip=skip, limit=limit, is_active=is_active)
    total = len(categories)
    
    return CategoryList(total=total, items=categories)
