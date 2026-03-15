from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.supplier_document import SupplierDocument
from app.schemas.supplier_document import SupplierDocumentCreate, SupplierDocumentUpdate


class CRUDSupplierDocument:
    """CRUD operations for SupplierDocument model."""

    def get(self, db: Session, document_id: int) -> Optional[SupplierDocument]:
        """Get a single supplier document by ID."""
        return db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()

    def get_by_supplier(
        self,
        db: Session,
        supplier_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SupplierDocument]:
        """Get all documents for a supplier."""
        return (
            db.query(SupplierDocument)
            .filter(SupplierDocument.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_supplier(self, db: Session, supplier_id: int) -> int:
        """Count documents for a supplier."""
        return db.query(SupplierDocument).filter(SupplierDocument.supplier_id == supplier_id).count()

    def create(self, db: Session, document_in: SupplierDocumentCreate) -> SupplierDocument:
        """Create a new supplier document."""
        db_document = SupplierDocument(
            supplier_id=document_in.supplier_id,
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
                detail="Database integrity error. Check that supplier_id and user IDs exist."
            )

    def update(
        self,
        db: Session,
        document_id: int,
        document_in: SupplierDocumentUpdate
    ) -> Optional[SupplierDocument]:
        """Update an existing supplier document."""
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

    def delete(self, db: Session, document_id: int) -> Optional[SupplierDocument]:
        """Delete a supplier document."""
        db_document = self.get(db, document_id)
        if not db_document:
            return None
        db.delete(db_document)
        db.commit()
        return db_document


supplier_document = CRUDSupplierDocument()
