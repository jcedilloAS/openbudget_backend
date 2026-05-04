from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.requisition_document import RequisitionDocument
from app.schemas.requisition_document import RequisitionDocumentCreate, RequisitionDocumentUpdate


class CRUDRequisitionDocument:
    """CRUD operations for RequisitionDocument model."""

    def get(self, db: Session, document_id: int) -> Optional[RequisitionDocument]:
        """Get a single requisition document by ID."""
        return db.query(RequisitionDocument).filter(RequisitionDocument.id == document_id).first()

    def get_by_requisition(
        self,
        db: Session,
        requisition_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[RequisitionDocument]:
        """Get all documents for a requisition."""
        return (
            db.query(RequisitionDocument)
            .filter(RequisitionDocument.requisition_id == requisition_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_requisition(self, db: Session, requisition_id: int) -> int:
        """Count documents for a requisition."""
        return db.query(RequisitionDocument).filter(RequisitionDocument.requisition_id == requisition_id).count()

    def create(self, db: Session, document_in: RequisitionDocumentCreate) -> RequisitionDocument:
        """Create a new requisition document."""
        db_document = RequisitionDocument(
            requisition_id=document_in.requisition_id,
            description=document_in.description,
            document_url=document_in.document_url,
            created_by=document_in.created_by,
            updated_by=document_in.updated_by,
        )
        try:
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            return db_document
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error. Check that requisition_id and user IDs exist."
            )

    def update(
        self,
        db: Session,
        document_id: int,
        document_in: RequisitionDocumentUpdate
    ) -> Optional[RequisitionDocument]:
        """Update an existing requisition document."""
        db_document = self.get(db, document_id)
        if not db_document:
            return None

        update_data = document_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_document, field, value)

        try:
            db.commit()
            db.refresh(db_document)
            return db_document
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error. Check that user IDs exist."
            )

    def delete(self, db: Session, document_id: int) -> Optional[RequisitionDocument]:
        """Delete a requisition document record (file deletion handled at endpoint level)."""
        db_document = self.get(db, document_id)
        if not db_document:
            return None
        db.delete(db_document)
        db.commit()
        return db_document


requisition_document = CRUDRequisitionDocument()
