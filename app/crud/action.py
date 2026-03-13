from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.action import Action
from app.schemas.action import ActionCreate, ActionUpdate
from app.utils.audit import AuditLogger


class CRUDAction:
    """CRUD operations for Action model."""
    
    def get(self, db: Session, action_id: int) -> Optional[Action]:
        """Get a single action by ID."""
        return db.query(Action).filter(Action.id == action_id).first()
    
    def get_by_action_code(self, db: Session, action_code: str) -> Optional[Action]:
        """Get a single action by action code."""
        return db.query(Action).filter(Action.action_code == action_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Action]:
        """Get multiple actions with pagination and optional filtering."""
        query = db.query(Action)
        
        if is_active is not None:
            query = query.filter(Action.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """Count total actions with optional filtering."""
        query = db.query(Action)
        
        if is_active is not None:
            query = query.filter(Action.is_active == is_active)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        action_in: ActionCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Action:
        """Create a new action."""
        # Check if action_code already exists
        existing_action = self.get_by_action_code(db, action_in.action_code)
        if existing_action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action with code '{action_in.action_code}' already exists"
            )
        
        db_action = Action(
            action_code=action_in.action_code,
            action_name=action_in.action_name,
            description=action_in.description,
            is_active=action_in.is_active
        )
        
        try:
            db.add(db_action)
            db.commit()
            db.refresh(db_action)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="actions",
                description=f"Created action: {db_action.action_code}",
                ip_address=ip_address,
                new_data={
                    "id": db_action.id,
                    "action_code": db_action.action_code,
                    "action_name": db_action.action_name,
                    "description": db_action.description,
                    "is_active": db_action.is_active
                },
                status="SUCCESS"
            )
            
            return db_action
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="actions",
                description=f"Failed to create action: {action_in.action_code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating action: {str(e)}"
            )
    
    def update(
        self,
        db: Session,
        action_id: int,
        action_in: ActionUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Action]:
        """Update an existing action."""
        db_action = self.get(db, action_id)
        
        if not db_action:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_action.id,
            "action_code": db_action.action_code,
            "action_name": db_action.action_name,
            "description": db_action.description,
            "is_active": db_action.is_active
        }
        
        # Check if new action_code already exists (if being updated)
        if action_in.action_code and action_in.action_code != db_action.action_code:
            existing_action = self.get_by_action_code(db, action_in.action_code)
            if existing_action:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Action with code '{action_in.action_code}' already exists"
                )
        
        # Update only provided fields
        update_data = action_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_action, field, value)
        
        try:
            db.commit()
            db.refresh(db_action)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="actions",
                description=f"Updated action: {db_action.action_code}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_action.id,
                    "action_code": db_action.action_code,
                    "action_name": db_action.action_name,
                    "description": db_action.description,
                    "is_active": db_action.is_active
                },
                status="SUCCESS"
            )
            
            return db_action
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="actions",
                description=f"Failed to update action ID: {action_id}",
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
        action_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Action]:
        """Delete an action."""
        db_action = self.get(db, action_id)
        
        if not db_action:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_action.id,
            "action_code": db_action.action_code,
            "action_name": db_action.action_name,
            "description": db_action.description,
            "is_active": db_action.is_active
        }
        
        db.delete(db_action)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="actions",
            description=f"Deleted action: {old_data['action_code']} (ID: {action_id})",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_action
    
    def soft_delete(
        self, 
        db: Session, 
        action_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Action]:
        """Soft delete an action by setting is_active to False."""
        db_action = self.get(db, action_id)
        
        if not db_action:
            return None
        
        old_status = db_action.is_active
        db_action.is_active = False
        db.commit()
        db.refresh(db_action)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="actions",
            description=f"Soft deleted action: {db_action.action_code} (ID: {action_id})",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_action
    
    def search(
        self,
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Action]:
        """Search actions by action_code or action_name."""
        query = db.query(Action)
        
        if is_active is not None:
            query = query.filter(Action.is_active == is_active)
        
        # Search in action_code or action_name
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Action.action_code.ilike(search_pattern)) |
            (Action.action_name.ilike(search_pattern))
        )
        
        return query.offset(skip).limit(limit).all()


# Create a singleton instance
action = CRUDAction()
