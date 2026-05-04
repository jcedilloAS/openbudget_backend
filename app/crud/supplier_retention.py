from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.supplier_retention import SupplierRetention
from app.schemas.supplier_retention import SupplierRetentionCreate


class CRUDSupplierRetention:
    """CRUD operations for SupplierRetention model."""

    def get(self, db: Session, record_id: int) -> Optional[SupplierRetention]:
        return (
            db.query(SupplierRetention)
            .options(joinedload(SupplierRetention.retention))
            .filter(SupplierRetention.id == record_id)
            .first()
        )

    def get_by_supplier(
        self, db: Session, supplier_id: int, skip: int = 0, limit: int = 100
    ) -> List[SupplierRetention]:
        return (
            db.query(SupplierRetention)
            .options(joinedload(SupplierRetention.retention))
            .filter(SupplierRetention.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_supplier(self, db: Session, supplier_id: int) -> int:
        return (
            db.query(SupplierRetention)
            .filter(SupplierRetention.supplier_id == supplier_id)
            .count()
        )

    def create(
        self, db: Session, record_in: SupplierRetentionCreate, user_id: int
    ) -> SupplierRetention:
        db_record = SupplierRetention(
            supplier_id=record_in.supplier_id,
            retention_id=record_in.retention_id,
            created_by=user_id,
            updated_by=user_id,
        )
        try:
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            return self.get(db, db_record.id)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This retention is already assigned to the supplier, or the supplier/retention does not exist.",
            )

    def delete(self, db: Session, record_id: int) -> bool:
        db_record = db.query(SupplierRetention).filter(SupplierRetention.id == record_id).first()
        if not db_record:
            return False
        db.delete(db_record)
        db.commit()
        return True


supplier_retention = CRUDSupplierRetention()
