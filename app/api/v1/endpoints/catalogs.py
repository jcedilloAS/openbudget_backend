from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.catalog import catalog
from app.schemas.catalog import Catalog, CatalogCreate, CatalogUpdate, CatalogList
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=CatalogList, summary="List all catalogs")
def list_catalogs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalogs", "list"))
):
    """
    Retrieve a list of catalogs with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    catalogs = catalog.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    total = catalog.count(db, is_active=is_active)
    
    return CatalogList(total=total, items=catalogs)


@router.get("/{catalog_id}", response_model=Catalog, summary="Get catalog by ID")
def get_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalogs", "list"))
):
    """
    Retrieve a specific catalog by ID.
    
    - **catalog_id**: The ID of the catalog to retrieve
    """
    db_catalog = catalog.get(db, catalog_id=catalog_id)
    
    if not db_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog with id {catalog_id} not found"
        )
    
    return db_catalog


@router.post("/", response_model=Catalog, status_code=status.HTTP_201_CREATED, summary="Create new catalog")
def create_catalog(
    catalog_in: CatalogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalogs", "create"))
):
    """
    Create a new catalog.
    
    - **catalog_code**: Unique catalog code (required)
    - **catalog_name**: Catalog name (required)
    - **description**: Optional description of the catalog
    - **is_active**: Whether the catalog is active (default: true)
    """
    ip_address = get_client_ip(request)
    return catalog.create(
        db, 
        catalog_in=catalog_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{catalog_id}", response_model=Catalog, summary="Update catalog")
def update_catalog(
    catalog_id: int,
    catalog_in: CatalogUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalogs", "update"))
):
    """
    Update an existing catalog.
    
    - **catalog_id**: The ID of the catalog to update
    - **catalog_code**: New catalog code (optional)
    - **catalog_name**: New name (optional)
    - **description**: New description (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_catalog = catalog.update(
        db, 
        catalog_id=catalog_id, 
        catalog_in=catalog_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog with id {catalog_id} not found"
        )
    
    return db_catalog


@router.delete("/{catalog_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete catalog")
def delete_catalog(
    catalog_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalogs", "delete"))
):
    """
    Delete a catalog.
    
    - **catalog_id**: The ID of the catalog to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_catalog = catalog.soft_delete(
            db, 
            catalog_id=catalog_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_catalog = catalog.delete(
            db, 
            catalog_id=catalog_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog with id {catalog_id} not found"
        )
    
    return None


@router.get("/search/", response_model=CatalogList, summary="Search catalogs")
def search_catalogs(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("catalogs", "list"))
):
    """
    Search catalogs by catalog_code or catalog_name.
    
    - **q**: Search term (required)
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    catalogs = catalog.search(db, search_term=q, skip=skip, limit=limit, is_active=is_active)
    total = len(catalogs)
    
    return CatalogList(total=total, items=catalogs)
