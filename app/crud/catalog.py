from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.catalog import Catalog
from app.schemas.catalog import CatalogCreate, CatalogUpdate
from app.utils.audit import AuditLogger


class CRUDCatalog:
    """CRUD operations for Catalog model."""
    
    def get(self, db: Session, catalog_id: int) -> Optional[Catalog]:
        """Get a single catalog by ID."""
        return db.query(Catalog).filter(Catalog.id == catalog_id).first()
    
    def get_by_catalog_code(self, db: Session, catalog_code: str) -> Optional[Catalog]:
        """Get a single catalog by catalog code."""
        return db.query(Catalog).filter(Catalog.catalog_code == catalog_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Catalog]:
        """Get multiple catalogs with pagination and optional filtering."""
        query = db.query(Catalog)
        
        if is_active is not None:
            query = query.filter(Catalog.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """Count total catalogs with optional filtering."""
        query = db.query(Catalog)
        
        if is_active is not None:
            query = query.filter(Catalog.is_active == is_active)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        catalog_in: CatalogCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Catalog:
        """Create a new catalog."""
        # Check if catalog_code already exists
        existing_catalog = self.get_by_catalog_code(db, catalog_in.catalog_code)
        if existing_catalog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Catalog with code '{catalog_in.catalog_code}' already exists"
            )
        
        db_catalog = Catalog(
            catalog_code=catalog_in.catalog_code,
            catalog_name=catalog_in.catalog_name,
            description=catalog_in.description,
            is_active=catalog_in.is_active
        )
        
        try:
            db.add(db_catalog)
            db.commit()
            db.refresh(db_catalog)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="catalogs",
                description=f"Created catalog: {db_catalog.catalog_code}",
                ip_address=ip_address,
                new_data={
                    "id": db_catalog.id,
                    "catalog_code": db_catalog.catalog_code,
                    "catalog_name": db_catalog.catalog_name,
                    "description": db_catalog.description,
                    "is_active": db_catalog.is_active
                },
                status="SUCCESS"
            )
            
            return db_catalog
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="catalogs",
                description=f"Failed to create catalog: {catalog_in.catalog_code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating catalog: {str(e)}"
            )
    
    def update(
        self,
        db: Session,
        catalog_id: int,
        catalog_in: CatalogUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Catalog]:
        """Update an existing catalog."""
        db_catalog = self.get(db, catalog_id)
        
        if not db_catalog:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_catalog.id,
            "catalog_code": db_catalog.catalog_code,
            "catalog_name": db_catalog.catalog_name,
            "description": db_catalog.description,
            "is_active": db_catalog.is_active
        }
        
        # Check if new catalog_code already exists (if being updated)
        if catalog_in.catalog_code and catalog_in.catalog_code != db_catalog.catalog_code:
            existing_catalog = self.get_by_catalog_code(db, catalog_in.catalog_code)
            if existing_catalog:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Catalog with code '{catalog_in.catalog_code}' already exists"
                )
        
        # Update only provided fields
        update_data = catalog_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_catalog, field, value)
        
        try:
            db.commit()
            db.refresh(db_catalog)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="catalogs",
                description=f"Updated catalog: {db_catalog.catalog_code}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_catalog.id,
                    "catalog_code": db_catalog.catalog_code,
                    "catalog_name": db_catalog.catalog_name,
                    "description": db_catalog.description,
                    "is_active": db_catalog.is_active
                },
                status="SUCCESS"
            )
            
            return db_catalog
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="catalogs",
                description=f"Failed to update catalog ID: {catalog_id}",
                ip_address=ip_address,
                status="FAILURE"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred"
            )
    
    def delete(
        self, 
        db: Session, 
        catalog_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Catalog]:
        """Delete a catalog."""
        db_catalog = self.get(db, catalog_id)
        
        if not db_catalog:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_catalog.id,
            "catalog_code": db_catalog.catalog_code,
            "catalog_name": db_catalog.catalog_name,
            "description": db_catalog.description,
            "is_active": db_catalog.is_active
        }
        
        db.delete(db_catalog)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="catalogs",
            description=f"Deleted catalog: {old_data['catalog_code']} (ID: {catalog_id})",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_catalog
    
    def soft_delete(
        self, 
        db: Session, 
        catalog_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Catalog]:
        """Soft delete a catalog by setting is_active to False."""
        db_catalog = self.get(db, catalog_id)
        
        if not db_catalog:
            return None
        
        old_status = db_catalog.is_active
        db_catalog.is_active = False
        db.commit()
        db.refresh(db_catalog)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="catalogs",
            description=f"Soft deleted catalog: {db_catalog.catalog_code} (ID: {catalog_id})",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_catalog
    
    def search(
        self,
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Catalog]:
        """Search catalogs by catalog_code or catalog_name."""
        query = db.query(Catalog)
        
        if is_active is not None:
            query = query.filter(Catalog.is_active == is_active)
        
        # Search in catalog_code or catalog_name
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Catalog.catalog_code.ilike(search_pattern)) |
            (Catalog.catalog_name.ilike(search_pattern))
        )
        
        return query.offset(skip).limit(limit).all()


# Create a singleton instance
catalog = CRUDCatalog()
