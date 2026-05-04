from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.category import Category
from app.models.supplier import Supplier
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.audit import AuditLogger


class CRUDCategory:
    """CRUD operations for Category model."""
    
    def get(self, db: Session, category_id: int) -> Optional[Category]:
        """Get a single category by ID."""
        return db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Category]:
        """Get a single category by name."""
        return db.query(Category).filter(Category.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Category]:
        """Get multiple categories with pagination and optional filtering."""
        query = db.query(Category)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """Count total categories with optional filtering."""
        query = db.query(Category)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        return query.count()
    
    def is_in_use(self, db: Session, category_id: int) -> bool:
        """Check if category is being used by any supplier."""
        count = db.query(Supplier).filter(Supplier.category_id == category_id).count()
        return count > 0
    
    def create(
        self, 
        db: Session, 
        category_in: CategoryCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Category:
        """Create a new category."""
        # Check if name already exists
        existing_category = self.get_by_name(db, category_in.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category_in.name}' already exists"
            )
        
        db_category = Category(
            name=category_in.name,
            description=category_in.description,
            is_active=category_in.is_active
        )
        
        try:
            db.add(db_category)
            db.commit()
            db.refresh(db_category)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="categories",
                description=f"Created category: {db_category.name}",
                ip_address=ip_address,
                new_data={
                    "id": db_category.id,
                    "name": db_category.name,
                    "description": db_category.description,
                    "is_active": db_category.is_active
                },
                status="SUCCESS"
            )
            
            return db_category
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="categories",
                description=f"Failed to create category: {category_in.name}",
                ip_address=ip_address,
                status="FAILURE"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating category: {str(e)}"
            )
    
    def update(
        self,
        db: Session,
        category_id: int,
        category_in: CategoryUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Category]:
        """Update an existing category."""
        db_category = self.get(db, category_id)
        
        if not db_category:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_category.id,
            "name": db_category.name,
            "description": db_category.description,
            "is_active": db_category.is_active
        }
        
        # Check if new name already exists (if being updated)
        if category_in.name and category_in.name != db_category.name:
            existing_category = self.get_by_name(db, category_in.name)
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with name '{category_in.name}' already exists"
                )
        
        # Update only provided fields
        update_data = category_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        try:
            db.commit()
            db.refresh(db_category)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="categories",
                description=f"Updated category: {db_category.name}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_category.id,
                    "name": db_category.name,
                    "description": db_category.description,
                    "is_active": db_category.is_active
                },
                status="SUCCESS"
            )
            
            return db_category
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="categories",
                description=f"Failed to update category ID: {category_id}",
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
        category_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Category]:
        """Delete a category (hard delete)."""
        db_category = self.get(db, category_id)
        
        if not db_category:
            return None
        
        # Check if category is in use
        if self.is_in_use(db, category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category is in use by one or more suppliers and cannot be deleted"
            )
        
        # Store data before deletion
        old_data = {
            "id": db_category.id,
            "name": db_category.name,
            "description": db_category.description,
            "is_active": db_category.is_active
        }
        
        db.delete(db_category)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="categories",
            description=f"Deleted category: {old_data['name']} (ID: {category_id})",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_category
    
    def soft_delete(
        self, 
        db: Session, 
        category_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Category]:
        """Soft delete a category by setting is_active to False."""
        db_category = self.get(db, category_id)
        
        if not db_category:
            return None
        
        # Check if category is in use
        if self.is_in_use(db, category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category is in use by one or more suppliers and cannot be deactivated"
            )
        
        old_status = db_category.is_active
        db_category.is_active = False
        db.commit()
        db.refresh(db_category)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="categories",
            description=f"Soft deleted category: {db_category.name} (ID: {category_id})",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_category
    
    def search(
        self,
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Category]:
        """Search categories by name or description."""
        query = db.query(Category)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        # Search in name or description
        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Category.name.ilike(search_pattern)) |
            (Category.description.ilike(search_pattern))
        )
        
        return query.offset(skip).limit(limit).all()


# Create a singleton instance
category = CRUDCategory()
