from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.requisition_retention import RequisitionRetention
from app.schemas.requisition_retention import RequisitionRetentionCreate, RequisitionRetentionUpdate


class CRUDRequisitionRetention:
    """CRUD operations for RequisitionRetention model."""

    def get(self, db: Session, record_id: int) -> Optional[RequisitionRetention]:
        return (
            db.query(RequisitionRetention)
            .options(joinedload(RequisitionRetention.retention))
            .filter(RequisitionRetention.id == record_id)
            .first()
        )

    def get_by_requisition(
        self, db: Session, requisition_id: int, skip: int = 0, limit: int = 100
    ) -> List[RequisitionRetention]:
        return (
            db.query(RequisitionRetention)
            .options(joinedload(RequisitionRetention.retention))
            .filter(RequisitionRetention.requisition_id == requisition_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_requisition(self, db: Session, requisition_id: int) -> int:
        return (
            db.query(RequisitionRetention)
            .filter(RequisitionRetention.requisition_id == requisition_id)
            .count()
        )

    def create(
        self, db: Session, record_in: RequisitionRetentionCreate, user_id: int
    ) -> RequisitionRetention:
        db_record = RequisitionRetention(
            requisition_id=record_in.requisition_id,
            retention_id=record_in.retention_id,
            retention_amount=record_in.retention_amount,
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
                detail="This retention is already applied to the requisition, or the requisition/retention does not exist.",
            )

    def update(
        self, db: Session, record_id: int, record_in: RequisitionRetentionUpdate, user_id: int
    ) -> Optional[RequisitionRetention]:
        db_record = db.query(RequisitionRetention).filter(RequisitionRetention.id == record_id).first()
        if not db_record:
            return None
        db_record.retention_amount = record_in.retention_amount
        db_record.updated_by = user_id
        db.commit()
        db.refresh(db_record)
        return self.get(db, db_record.id)

    def delete(self, db: Session, record_id: int) -> bool:
        db_record = db.query(RequisitionRetention).filter(RequisitionRetention.id == record_id).first()
        if not db_record:
            return False
        db.delete(db_record)
        db.commit()
        return True

    def delete_by_requisition(self, db: Session, requisition_id: int) -> None:
        db.query(RequisitionRetention).filter(
            RequisitionRetention.requisition_id == requisition_id
        ).delete()


requisition_retention = CRUDRequisitionRetention()
