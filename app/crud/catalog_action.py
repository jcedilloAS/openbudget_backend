from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.catalog_action import CatalogAction
from app.models.catalog import Catalog
from app.models.action import Action
from app.schemas.catalog_action import CatalogActionCreate, CatalogActionUpdate, CatalogActionWithDetails
from app.utils.audit import AuditLogger


class CRUDCatalogAction:
    """CRUD operations for CatalogAction model."""
    
    def get(self, db: Session, catalog_action_id: int) -> Optional[CatalogAction]:
        """Get a single catalog-action by ID."""
        return db.query(CatalogAction).filter(CatalogAction.id == catalog_action_id).first()
    
    def get_by_catalog_and_action(
        self, 
        db: Session, 
        catalog_id: int, 
        action_id: int
    ) -> Optional[CatalogAction]:
        """Get a catalog-action by catalog_id and action_id."""
        return db.query(CatalogAction).filter(
            and_(
                CatalogAction.catalog_id == catalog_id,
                CatalogAction.action_id == action_id
            )
        ).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        catalog_id: Optional[int] = None,
        action_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[CatalogAction]:
        """Get multiple catalog-actions with pagination and optional filtering."""
        query = db.query(CatalogAction)
        
        if catalog_id is not None:
            query = query.filter(CatalogAction.catalog_id == catalog_id)
        
        if action_id is not None:
            query = query.filter(CatalogAction.action_id == action_id)
        
        if is_active is not None:
            query = query.filter(CatalogAction.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_multi_with_details(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        catalog_id: Optional[int] = None,
        action_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[CatalogActionWithDetails]:
        """Get multiple catalog-actions with catalog and action details."""
        query = db.query(
            CatalogAction.id,
            CatalogAction.catalog_id,
            CatalogAction.action_id,
            CatalogAction.is_active,
            CatalogAction.created_at,
            Catalog.catalog_code,
            Catalog.catalog_name,
            Action.action_code,
            Action.action_name
        ).join(
            Catalog, CatalogAction.catalog_id == Catalog.id
        ).join(
            Action, CatalogAction.action_id == Action.id
        )
        
        if catalog_id is not None:
            query = query.filter(CatalogAction.catalog_id == catalog_id)
        
        if action_id is not None:
            query = query.filter(CatalogAction.action_id == action_id)
        
        if is_active is not None:
            query = query.filter(CatalogAction.is_active == is_active)
        
        results = query.offset(skip).limit(limit).all()
        
        return [
            CatalogActionWithDetails(
                id=r.id,
                catalog_id=r.catalog_id,
                action_id=r.action_id,
                is_active=r.is_active,
                created_at=r.created_at,
                catalog_code=r.catalog_code,
                catalog_name=r.catalog_name,
                action_code=r.action_code,
                action_name=r.action_name
            )
            for r in results
        ]
    
    def count(
        self, 
        db: Session, 
        catalog_id: Optional[int] = None,
        action_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Count total catalog-actions with optional filtering."""
        query = db.query(CatalogAction)
        
        if catalog_id is not None:
            query = query.filter(CatalogAction.catalog_id == catalog_id)
        
        if action_id is not None:
            query = query.filter(CatalogAction.action_id == action_id)
        
        if is_active is not None:
            query = query.filter(CatalogAction.is_active == is_active)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        catalog_action_in: CatalogActionCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> CatalogAction:
        """Create a new catalog-action relationship."""
        # Check if relationship already exists
        existing = self.get_by_catalog_and_action(
            db, 
            catalog_action_in.catalog_id, 
            catalog_action_in.action_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Relationship between catalog {catalog_action_in.catalog_id} and action {catalog_action_in.action_id} already exists"
            )
        
        # Verify catalog exists
        catalog = db.query(Catalog).filter(Catalog.id == catalog_action_in.catalog_id).first()
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catalog with id {catalog_action_in.catalog_id} not found"
            )
        
        # Verify action exists
        action = db.query(Action).filter(Action.id == catalog_action_in.action_id).first()
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with id {catalog_action_in.action_id} not found"
            )
        
        db_catalog_action = CatalogAction(
            catalog_id=catalog_action_in.catalog_id,
            action_id=catalog_action_in.action_id,
            is_active=catalog_action_in.is_active
        )
        
        try:
            db.add(db_catalog_action)
            db.commit()
            db.refresh(db_catalog_action)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="catalog_actions",
                description=f"Created catalog-action: catalog_id={db_catalog_action.catalog_id}, action_id={db_catalog_action.action_id}",
                ip_address=ip_address,
                new_data={
                    "id": db_catalog_action.id,
                    "catalog_id": db_catalog_action.catalog_id,
                    "action_id": db_catalog_action.action_id,
                    "is_active": db_catalog_action.is_active
                },
                status="SUCCESS"
            )
            
            return db_catalog_action
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="catalog_actions",
                description=f"Failed to create catalog-action",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating catalog-action: {str(e)}"
            )
    
    def update(
        self,
        db: Session,
        catalog_action_id: int,
        catalog_action_in: CatalogActionUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[CatalogAction]:
        """Update an existing catalog-action."""
        db_catalog_action = self.get(db, catalog_action_id)
        
        if not db_catalog_action:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_catalog_action.id,
            "catalog_id": db_catalog_action.catalog_id,
            "action_id": db_catalog_action.action_id,
            "is_active": db_catalog_action.is_active
        }
        
        # Update only provided fields
        update_data = catalog_action_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_catalog_action, field, value)
        
        try:
            db.commit()
            db.refresh(db_catalog_action)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="catalog_actions",
                description=f"Updated catalog-action ID: {catalog_action_id}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_catalog_action.id,
                    "catalog_id": db_catalog_action.catalog_id,
                    "action_id": db_catalog_action.action_id,
                    "is_active": db_catalog_action.is_active
                },
                status="SUCCESS"
            )
            
            return db_catalog_action
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="catalog_actions",
                description=f"Failed to update catalog-action ID: {catalog_action_id}",
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
        catalog_action_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[CatalogAction]:
        """Delete a catalog-action."""
        db_catalog_action = self.get(db, catalog_action_id)
        
        if not db_catalog_action:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_catalog_action.id,
            "catalog_id": db_catalog_action.catalog_id,
            "action_id": db_catalog_action.action_id,
            "is_active": db_catalog_action.is_active
        }
        
        db.delete(db_catalog_action)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="catalog_actions",
            description=f"Deleted catalog-action ID: {catalog_action_id}",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_catalog_action
    
    def soft_delete(
        self, 
        db: Session, 
        catalog_action_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[CatalogAction]:
        """Soft delete a catalog-action by setting is_active to False."""
        db_catalog_action = self.get(db, catalog_action_id)
        
        if not db_catalog_action:
            return None
        
        old_status = db_catalog_action.is_active
        db_catalog_action.is_active = False
        db.commit()
        db.refresh(db_catalog_action)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="catalog_actions",
            description=f"Soft deleted catalog-action ID: {catalog_action_id}",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_catalog_action


# Create a singleton instance
catalog_action = CRUDCatalogAction()
