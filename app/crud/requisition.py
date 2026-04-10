from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime

from app.models.requisition import Requisition
from app.models.requisition_item import RequisitionItem
from app.models.project import Project
from app.schemas.requisition import RequisitionCreate, RequisitionUpdate


class CRUDRequisition:
    """CRUD operations for Requisition model."""
    
    def get(self, db: Session, requisition_id: int) -> Optional[Requisition]:
        """Get a single requisition by ID."""
        return db.query(Requisition).filter(Requisition.id == requisition_id).first()
    
    def get_by_requisition_number(self, db: Session, requisition_number: str) -> Optional[Requisition]:
        """Get a single requisition by requisition number."""
        return db.query(Requisition).filter(Requisition.requisition_number == requisition_number).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        project_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        requested_by: Optional[int] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> List[Requisition]:
        """Get multiple requisitions with pagination and optional filtering."""
        query = db.query(Requisition)
        
        if project_id is not None:
            query = query.filter(Requisition.project_id == project_id)
        
        if supplier_id is not None:
            query = query.filter(Requisition.supplier_id == supplier_id)
        
        if requested_by is not None:
            query = query.filter(Requisition.requested_by == requested_by)
        
        if status is not None:
            query = query.filter(Requisition.status == status)
        
        if created_by is not None:
            query = query.filter(Requisition.created_by == created_by)
        
        return query.order_by(Requisition.created_at.desc()).offset(skip).limit(limit).all()
    
    def count(
        self, 
        db: Session,
        project_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        requested_by: Optional[int] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """Count total requisitions with optional filtering."""
        query = db.query(Requisition)
        
        if project_id is not None:
            query = query.filter(Requisition.project_id == project_id)
        
        if supplier_id is not None:
            query = query.filter(Requisition.supplier_id == supplier_id)
        
        if requested_by is not None:
            query = query.filter(Requisition.requested_by == requested_by)
        
        if status is not None:
            query = query.filter(Requisition.status == status)
        
        if created_by is not None:
            query = query.filter(Requisition.created_by == created_by)
        
        return query.count()
    
    def create(self, db: Session, requisition_in: RequisitionCreate, user_id: int) -> Requisition:
        """Create a new requisition."""
        # Check if requisition number already exists
        existing_requisition = self.get_by_requisition_number(db, requisition_in.requisition_number)
        if existing_requisition:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requisition with number '{requisition_in.requisition_number}' already exists"
            )
        
        requisition_data = requisition_in.model_dump(exclude={"items"})
        db_requisition = Requisition(
            **requisition_data,
            created_by=user_id,
            updated_by=user_id
        )
        
        try:
            db.add(db_requisition)
            db.flush()
            
            # Create items if provided
            if requisition_in.items:
                for item_data in requisition_in.items:
                    db_item = RequisitionItem(
                        requisition_id=db_requisition.id,
                        item_name=item_data.item_name,
                        description=item_data.description,
                        quantity=item_data.quantity,
                        unit=item_data.unit,
                        unit_price=item_data.unit_price,
                        total_amount=item_data.total_amount
                    )
                    db.add(db_item)
            
            db.commit()
            db.refresh(db_requisition)
            return db_requisition
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if project_id, supplier_id, and user IDs exist."
            )
    
    def update(
        self, 
        db: Session, 
        requisition_id: int, 
        requisition_in: RequisitionUpdate,
        user_id: int
    ) -> Optional[Requisition]:
        """Update an existing requisition."""
        db_requisition = self.get(db, requisition_id)
        
        if not db_requisition:
            return None
        
        # Only draft requisitions can be edited
        if db_requisition.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update requisition with status '{db_requisition.status}'"
            )
        
        update_data = requisition_in.model_dump(exclude_unset=True, exclude={"items"})
        
        # Check if requisition_number is being changed and if it already exists
        if "requisition_number" in update_data and update_data["requisition_number"] != db_requisition.requisition_number:
            existing_requisition = self.get_by_requisition_number(db, update_data["requisition_number"])
            if existing_requisition:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Requisition with number '{update_data['requisition_number']}' already exists"
                )
        
        for field, value in update_data.items():
            setattr(db_requisition, field, value)
        
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()
        
        try:
            # Handle items update if provided
            if requisition_in.items is not None:
                # Delete all existing items
                db.query(RequisitionItem).filter(
                    RequisitionItem.requisition_id == requisition_id
                ).delete()
                
                # Create new items
                for item_data in requisition_in.items:
                    db_item = RequisitionItem(
                        requisition_id=db_requisition.id,
                        item_name=item_data.item_name,
                        description=item_data.description,
                        quantity=item_data.quantity,
                        unit=item_data.unit,
                        unit_price=item_data.unit_price,
                        total_amount=item_data.total_amount
                    )
                    db.add(db_item)
            
            db.commit()
            db.refresh(db_requisition)
            return db_requisition
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if project_id, supplier_id, and user IDs exist."
            )
    
    def delete(self, db: Session, requisition_id: int) -> bool:
        """Delete a requisition."""
        db_requisition = self.get(db, requisition_id)
        
        if not db_requisition:
            return False
        
        # Only draft requisitions can be deleted
        if db_requisition.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete requisition with status '{db_requisition.status}'"
            )
        
        db.delete(db_requisition)
        db.commit()
        return True
    
    def _update_project_budget(self, db: Session, project_id: int, commited_delta, spent_delta) -> None:
        """Adjust project commited/spent and recalculate available_balance."""
        project = db.query(Project).filter(Project.id == project_id).with_for_update().first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        project.commited = project.commited + commited_delta
        project.spent = project.spent + spent_delta
        project.available_balance = project.initial_budget - project.commited - project.spent

    def submit(self, db: Session, requisition_id: int, user_id: int) -> Optional[Requisition]:
        """Submit a draft requisition for approval. Commits the amount in the project."""
        db_requisition = self.get(db, requisition_id)

        if not db_requisition:
            return None

        if db_requisition.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit requisition with status '{db_requisition.status}'"
            )

        self._update_project_budget(db, db_requisition.project_id, db_requisition.total_amount, 0)

        db_requisition.status = "submitted"
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()

        db.commit()
        db.refresh(db_requisition)
        return db_requisition

    def cancel(self, db: Session, requisition_id: int, user_id: int) -> Optional[Requisition]:
        """Cancel a draft or submitted requisition. Reverses committed amount if submitted."""
        db_requisition = self.get(db, requisition_id)

        if not db_requisition:
            return None

        if db_requisition.status not in ["draft", "submitted"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel requisition with status '{db_requisition.status}'"
            )

        if db_requisition.status == "submitted":
            self._update_project_budget(db, db_requisition.project_id, -db_requisition.total_amount, 0)

        db_requisition.status = "cancelled"
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()

        db.commit()
        db.refresh(db_requisition)
        return db_requisition

    def approve(self, db: Session, requisition_id: int, user_id: int) -> Optional[Requisition]:
        """Approve a submitted requisition. Moves amount from commited to spent."""
        db_requisition = self.get(db, requisition_id)
        
        if not db_requisition:
            return None
        
        if db_requisition.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve requisition with status '{db_requisition.status}'"
            )

        self._update_project_budget(
            db, db_requisition.project_id,
            -db_requisition.total_amount,
            db_requisition.total_amount
        )
        
        db_requisition.status = "approved"
        db_requisition.approved_by = user_id
        db_requisition.approved_at = datetime.utcnow()
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()
        
        db.commit()
        db.refresh(db_requisition)
        return db_requisition
    
    def reject(self, db: Session, requisition_id: int, user_id: int, rejection_reason: str) -> Optional[Requisition]:
        """Reject a submitted requisition. Releases the committed amount."""
        db_requisition = self.get(db, requisition_id)
        
        if not db_requisition:
            return None
        
        if db_requisition.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject requisition with status '{db_requisition.status}'"
            )

        self._update_project_budget(db, db_requisition.project_id, -db_requisition.total_amount, 0)
        
        db_requisition.status = "rejected"
        db_requisition.rejected_by = user_id
        db_requisition.rejected_at = datetime.utcnow()
        db_requisition.rejection_reason = rejection_reason
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()
        
        db.commit()
        db.refresh(db_requisition)
        return db_requisition
    
    def search(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[Requisition]:
        """Search requisitions by requisition number."""
        return (
            db.query(Requisition)
            .filter(Requisition.requisition_number.ilike(f"%{search_term}%"))
            .order_by(Requisition.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


# Create a singleton instance
requisition = CRUDRequisition()
