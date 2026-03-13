from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.retention import Retention
from app.schemas.retention import RetentionCreate, RetentionUpdate
from app.utils.audit import AuditLogger


class CRUDRetention:
    """CRUD operations for Retention model."""
    
    def get(self, db: Session, retention_id: int) -> Optional[Retention]:
        """Get a single retention by ID."""
        return db.query(Retention).filter(Retention.id == retention_id).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[Retention]:
        """Get a single retention by code."""
        return db.query(Retention).filter(Retention.code == code).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Retention]:
        """Get multiple retentions with pagination and optional filtering."""
        query = db.query(Retention)
        
        if is_active is not None:
            query = query.filter(Retention.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """Count total retentions with optional filtering."""
        query = db.query(Retention)
        
        if is_active is not None:
            query = query.filter(Retention.is_active == is_active)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        retention_in: RetentionCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Retention:
        """Create a new retention."""
        # Check if code already exists
        existing_retention = self.get_by_code(db, retention_in.code)
        if existing_retention:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Retention with code '{retention_in.code}' already exists"
            )
        
        db_retention = Retention(
            code=retention_in.code,
            description=retention_in.description,
            percentage=retention_in.percentage,
            is_active=retention_in.is_active,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        try:
            db.add(db_retention)
            db.commit()
            db.refresh(db_retention)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="retentions",
                description=f"Created retention: {db_retention.code}",
                ip_address=ip_address,
                new_data={
                    "id": db_retention.id,
                    "code": db_retention.code,
                    "description": db_retention.description,
                    "percentage": float(db_retention.percentage),
                    "is_active": db_retention.is_active
                },
                status="SUCCESS"
            )
            
            return db_retention
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="retentions",
                description=f"Failed to create retention: {retention_in.code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating retention: {str(e)}"
            )
    
    def update(
        self,
        db: Session,
        retention_id: int,
        retention_in: RetentionUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Retention]:
        """Update an existing retention."""
        db_retention = self.get(db, retention_id)
        
        if not db_retention:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_retention.id,
            "code": db_retention.code,
            "description": db_retention.description,
            "percentage": float(db_retention.percentage),
            "is_active": db_retention.is_active
        }
        
        # Check if new code already exists (if being updated)
        if retention_in.code and retention_in.code != db_retention.code:
            existing_retention = self.get_by_code(db, retention_in.code)
            if existing_retention:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Retention with code '{retention_in.code}' already exists"
                )
        
        # Update only provided fields
        update_data = retention_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_retention, field, value)
        
        db_retention.updated_by = current_user_id
        
        try:
            db.commit()
            db.refresh(db_retention)
            
            # Store new data for audit
            new_data = {
                "id": db_retention.id,
                "code": db_retention.code,
                "description": db_retention.description,
                "percentage": float(db_retention.percentage),
                "is_active": db_retention.is_active
            }
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="retentions",
                description=f"Updated retention: {db_retention.code}",
                ip_address=ip_address,
                old_data=old_data,
                new_data=new_data,
                status="SUCCESS"
            )
            
            return db_retention
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="retentions",
                description=f"Failed to update retention: {db_retention.code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating retention: {str(e)}"
            )
    
    def soft_delete(
        self,
        db: Session,
        retention_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Retention]:
        """Soft delete a retention (set is_active to False)."""
        db_retention = self.get(db, retention_id)
        
        if not db_retention:
            return None
        
        old_is_active = db_retention.is_active
        db_retention.is_active = False
        db_retention.updated_by = current_user_id
        
        try:
            db.commit()
            db.refresh(db_retention)
            
            # Log the soft delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="SOFT_DELETE",
                module="retentions",
                description=f"Soft deleted retention: {db_retention.code}",
                ip_address=ip_address,
                old_data={"is_active": old_is_active},
                new_data={"is_active": False},
                status="SUCCESS"
            )
            
            return db_retention
            
        except Exception as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="SOFT_DELETE",
                module="retentions",
                description=f"Failed to soft delete retention: {db_retention.code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error soft deleting retention: {str(e)}"
            )
    
    def delete(
        self,
        db: Session,
        retention_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Retention]:
        """Hard delete a retention (permanent deletion)."""
        db_retention = self.get(db, retention_id)
        
        if not db_retention:
            return None
        
        # Store data for audit before deletion
        retention_data = {
            "id": db_retention.id,
            "code": db_retention.code,
            "description": db_retention.description,
            "percentage": float(db_retention.percentage),
            "is_active": db_retention.is_active
        }
        
        try:
            db.delete(db_retention)
            db.commit()
            
            # Log the delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="retentions",
                description=f"Deleted retention: {retention_data['code']}",
                ip_address=ip_address,
                old_data=retention_data,
                status="SUCCESS"
            )
            
            return db_retention
            
        except Exception as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="retentions",
                description=f"Failed to delete retention: {retention_data['code']}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting retention: {str(e)}"
            )


# Create instance
retention = CRUDRetention()
