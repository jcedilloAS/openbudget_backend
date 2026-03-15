from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class CRUDSupplier:
    """CRUD operations for Supplier model."""
    
    def get(self, db: Session, supplier_id: int) -> Optional[Supplier]:
        """Get a single supplier by ID."""
        return db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    def get_by_supplier_code(self, db: Session, supplier_code: str) -> Optional[Supplier]:
        """Get a single supplier by supplier code."""
        return db.query(Supplier).filter(Supplier.supplier_code == supplier_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        created_by: Optional[int] = None
    ) -> List[Supplier]:
        """Get multiple suppliers with pagination and optional filtering."""
        query = db.query(Supplier)
        
        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
        
        if created_by is not None:
            query = query.filter(Supplier.created_by == created_by)
        
        return query.offset(skip).limit(limit).all()
    
    def count(
        self, 
        db: Session, 
        is_active: Optional[bool] = None,
        created_by: Optional[int] = None
    ) -> int:
        """Count total suppliers with optional filtering."""
        query = db.query(Supplier)
        
        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
        
        if created_by is not None:
            query = query.filter(Supplier.created_by == created_by)
        
        return query.count()
    
    def create(self, db: Session, supplier_in: SupplierCreate, user_id: int) -> Supplier:
        """Create a new supplier."""
        # Check if supplier code already exists
        existing_supplier = self.get_by_supplier_code(db, supplier_in.supplier_code)
        if existing_supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with code '{supplier_in.supplier_code}' already exists"
            )
        
        db_supplier = Supplier(
            supplier_code=supplier_in.supplier_code,
            name=supplier_in.name,
            rfc=supplier_in.rfc,
            phone=supplier_in.phone,
            address=supplier_in.address,
            postal_code=supplier_in.postal_code,
            city=supplier_in.city,
            state=supplier_in.state,
            country=supplier_in.country,
            percentage_iva=supplier_in.percentage_iva,
            delivery_time_days=supplier_in.delivery_time_days,
            is_active=supplier_in.is_active,
            created_by=user_id,
            updated_by=user_id
        )
        
        try:
            db.add(db_supplier)
            db.commit()
            db.refresh(db_supplier)
            return db_supplier
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if user IDs exist."
            )
    
    def update(
        self, 
        db: Session, 
        supplier_id: int, 
        supplier_in: SupplierUpdate,
        user_id: int
    ) -> Optional[Supplier]:
        """Update an existing supplier."""
        db_supplier = self.get(db, supplier_id)
        
        if not db_supplier:
            return None
        
        # Check if new supplier code already exists (if being updated)
        if supplier_in.supplier_code and supplier_in.supplier_code != db_supplier.supplier_code:
            existing_supplier = self.get_by_supplier_code(db, supplier_in.supplier_code)
            if existing_supplier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Supplier with code '{supplier_in.supplier_code}' already exists"
                )
        
        # Update only provided fields
        update_data = supplier_in.model_dump(exclude_unset=True)
        update_data["updated_by"] = user_id
        
        for field, value in update_data.items():
            setattr(db_supplier, field, value)
        
        try:
            db.commit()
            db.refresh(db_supplier)
            return db_supplier
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if user IDs exist."
            )
    
    def delete(self, db: Session, supplier_id: int) -> Optional[Supplier]:
        """Delete a supplier."""
        db_supplier = self.get(db, supplier_id)
        
        if not db_supplier:
            return None
        
        db.delete(db_supplier)
        db.commit()
        return db_supplier
    
    def soft_delete(self, db: Session, supplier_id: int) -> Optional[Supplier]:
        """Soft delete a supplier by setting is_active to False."""
        db_supplier = self.get(db, supplier_id)
        
        if not db_supplier:
            return None
        
        db_supplier.is_active = False
        db.commit()
        db.refresh(db_supplier)
        return db_supplier
    
    def search(
        self, 
        db: Session, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Supplier]:
        """Search suppliers by name, code, or RFC."""
        search_pattern = f"%{search_term}%"
        return db.query(Supplier).filter(
            (Supplier.name.ilike(search_pattern)) |
            (Supplier.supplier_code.ilike(search_pattern)) |
            (Supplier.rfc.ilike(search_pattern))
        ).offset(skip).limit(limit).all()


supplier = CRUDSupplier()
