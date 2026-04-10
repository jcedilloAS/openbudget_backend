from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.requisition_item import RequisitionItem
from app.schemas.requisition_item import RequisitionItemCreate, RequisitionItemUpdate


class CRUDRequisitionItem:
    """CRUD operations for RequisitionItem model."""
    
    def get(self, db: Session, item_id: int) -> Optional[RequisitionItem]:
        """Get a single requisition item by ID."""
        return db.query(RequisitionItem).filter(RequisitionItem.id == item_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        requisition_id: Optional[int] = None
    ) -> List[RequisitionItem]:
        """Get multiple requisition items with pagination and optional filtering."""
        query = db.query(RequisitionItem)
        
        if requisition_id is not None:
            query = query.filter(RequisitionItem.requisition_id == requisition_id)
        
        return query.order_by(RequisitionItem.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_requisition(self, db: Session, requisition_id: int) -> List[RequisitionItem]:
        """Get all items for a specific requisition."""
        return db.query(RequisitionItem).filter(RequisitionItem.requisition_id == requisition_id).all()
    
    def count(
        self, 
        db: Session,
        requisition_id: Optional[int] = None
    ) -> int:
        """Count total requisition items with optional filtering."""
        query = db.query(RequisitionItem)
        
        if requisition_id is not None:
            query = query.filter(RequisitionItem.requisition_id == requisition_id)
        
        return query.count()
    
    def create(self, db: Session, item_in: RequisitionItemCreate, requisition_id: int) -> RequisitionItem:
        """Create a new requisition item."""
        item_data = item_in.model_dump()
        db_item = RequisitionItem(
            **item_data,
            requisition_id=requisition_id
        )
        
        try:
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            return db_item
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if requisition_id exists."
            )
    
    def update(
        self, 
        db: Session, 
        item_id: int, 
        item_in: RequisitionItemUpdate
    ) -> Optional[RequisitionItem]:
        """Update an existing requisition item."""
        db_item = self.get(db, item_id)
        
        if not db_item:
            return None
        
        update_data = item_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        try:
            db.commit()
            db.refresh(db_item)
            return db_item
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred."
            )
    
    def delete(self, db: Session, item_id: int) -> bool:
        """Delete a requisition item."""
        db_item = self.get(db, item_id)
        
        if not db_item:
            return False
        
        db.delete(db_item)
        db.commit()
        return True
    
    def delete_by_requisition(self, db: Session, requisition_id: int) -> int:
        """Delete all items for a specific requisition. Returns count of deleted items."""
        deleted_count = db.query(RequisitionItem).filter(
            RequisitionItem.requisition_id == requisition_id
        ).delete()
        db.commit()
        return deleted_count


# Create a singleton instance
requisition_item = CRUDRequisitionItem()
