from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import date, datetime

from app.models.requisition import Requisition
from app.models.requisition_item import RequisitionItem
from app.models.supplier import Supplier
from app.models.requisition_document import RequisitionDocument
from app.models.requisition_retention import RequisitionRetention
from app.models.project import Project
from app.schemas.requisition import RequisitionCreate, RequisitionUpdate, RequisitionAssignPurchaseOrder
from app.utils.audit import AuditLogger


class CRUDRequisition:
    """CRUD operations for Requisition model."""
    
    def get(self, db: Session, requisition_id: int) -> Optional[Requisition]:
        """Get a single requisition by ID."""
        return (
            db.query(Requisition)
            .options(
                joinedload(Requisition.items),
                joinedload(Requisition.documents),
                joinedload(Requisition.retentions).joinedload(RequisitionRetention.retention),
                joinedload(Requisition.supplier),
                joinedload(Requisition.creator),
            )
            .filter(Requisition.id == requisition_id)
            .first()
        )
    
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
        created_by: Optional[int] = None,
        viewer_id: Optional[int] = None
    ) -> List[Requisition]:
        """Get multiple requisitions with pagination and optional filtering."""
        query = db.query(Requisition)

        if project_id is not None:
            query = query.filter(Requisition.project_id == project_id)

        if supplier_id is not None:
            query = query.filter(Requisition.supplier_id == supplier_id)

        if viewer_id is not None:
            query = query.filter(
                or_(Requisition.requested_by == viewer_id, Requisition.created_by == viewer_id)
            )
        else:
            if requested_by is not None:
                query = query.filter(Requisition.requested_by == requested_by)
            if created_by is not None:
                query = query.filter(Requisition.created_by == created_by)

        if status is not None:
            query = query.filter(Requisition.status == status)
        
        return (
            query
            .options(
                joinedload(Requisition.supplier),
                joinedload(Requisition.project),
                joinedload(Requisition.creator),
            )
            .order_by(Requisition.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_for_export(
        self,
        db: Session,
        project_id: Optional[List[int]] = None,
        supplier_id: Optional[List[int]] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> List[Requisition]:
        query = db.query(Requisition)

        if project_id:
            query = query.filter(Requisition.project_id.in_(project_id))
        if supplier_id:
            query = query.filter(Requisition.supplier_id.in_(supplier_id))
        if status is not None:
            query = query.filter(Requisition.status == status)
        if created_by is not None:
            query = query.filter(Requisition.created_by == created_by)

        return (
            query
            .options(
                joinedload(Requisition.supplier),
                joinedload(Requisition.creator),
            )
            .order_by(Requisition.created_at.desc())
            .all()
        )

    def get_for_report(
        self,
        db: Session,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        supplier_id: Optional[List[int]] = None,
        project_id: Optional[List[int]] = None,
        status: Optional[str] = None,
    ) -> List[Requisition]:
        query = db.query(Requisition)

        if date_from is not None:
            query = query.filter(Requisition.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to is not None:
            query = query.filter(Requisition.created_at <= datetime.combine(date_to, datetime.max.time()))
        if supplier_id:
            query = query.filter(Requisition.supplier_id.in_(supplier_id))
        if project_id:
            query = query.filter(Requisition.project_id.in_(project_id))
        if status is not None:
            query = query.filter(Requisition.status == status)

        return (
            query
            .options(
                joinedload(Requisition.supplier),
                joinedload(Requisition.project),
                joinedload(Requisition.items).joinedload(RequisitionItem.account),
            )
            .order_by(Requisition.created_at.desc())
            .all()
        )

    def count(
        self,
        db: Session,
        project_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        requested_by: Optional[int] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        viewer_id: Optional[int] = None
    ) -> int:
        """Count total requisitions with optional filtering."""
        query = db.query(Requisition)

        if project_id is not None:
            query = query.filter(Requisition.project_id == project_id)

        if supplier_id is not None:
            query = query.filter(Requisition.supplier_id == supplier_id)

        if viewer_id is not None:
            query = query.filter(
                or_(Requisition.requested_by == viewer_id, Requisition.created_by == viewer_id)
            )
        else:
            if requested_by is not None:
                query = query.filter(Requisition.requested_by == requested_by)
            if created_by is not None:
                query = query.filter(Requisition.created_by == created_by)

        if status is not None:
            query = query.filter(Requisition.status == status)

        return query.count()
    
    def create(self, db: Session, requisition_in: RequisitionCreate, user_id: int, ip_address: Optional[str] = None) -> Requisition:
        """Create a new requisition."""
        # Import here to avoid circular imports
        from app.crud.system_configuration import system_configuration as sys_config_crud
        
        # Auto-generate requisition_number if not provided
        if not requisition_in.requisition_number:
            requisition_in.requisition_number = sys_config_crud.get_next_folio(db)
        
        # Check if requisition number already exists
        existing_requisition = self.get_by_requisition_number(db, requisition_in.requisition_number)
        if existing_requisition:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requisition with number '{requisition_in.requisition_number}' already exists"
            )
        
        # Validate supplier tax period has not expired
        if requisition_in.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == requisition_in.supplier_id).first()
            if supplier and supplier.tax_end_date and supplier.tax_end_date < date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"The tax rates for supplier '{supplier.name}' expired on "
                        f"{supplier.tax_end_date.isoformat()}. Update the supplier's tax period before creating a requisition."
                    ),
                )

        requisition_data = requisition_in.model_dump(exclude={"items", "documents", "retentions"})

        if requisition_data.get("currency") == "USD":
            from app.utils.banxico import fetch_usd_exchange_rate
            try:
                requisition_data["exchange_rate"] = fetch_usd_exchange_rate()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"No se pudo obtener el tipo de cambio de Banxico: {exc}",
                )

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

            # Create documents if provided
            if requisition_in.documents:
                for doc in requisition_in.documents:
                    if doc.document_url:
                        db_doc = RequisitionDocument(
                            requisition_id=db_requisition.id,
                            description=doc.description,
                            document_url=doc.document_url,
                            created_by=user_id,
                            updated_by=user_id
                        )
                        db.add(db_doc)

            # Create retentions if provided
            if requisition_in.retentions:
                for ret in requisition_in.retentions:
                    db_ret = RequisitionRetention(
                        requisition_id=db_requisition.id,
                        retention_id=ret.retention_id,
                        retention_amount=ret.retention_amount,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    db.add(db_ret)
            
            db.commit()
            db.refresh(db_requisition)
            AuditLogger.log_action(
                db=db,
                user_id=user_id,
                action="CREATE",
                module="requisitions",
                description=f"Created requisition: {db_requisition.requisition_number}",
                ip_address=ip_address,
                new_data={
                    "id": db_requisition.id,
                    "requisition_number": db_requisition.requisition_number,
                    "project_id": db_requisition.project_id,
                    "supplier_id": db_requisition.supplier_id,
                    "total_amount": float(db_requisition.total_amount),
                    "status": db_requisition.status,
                },
                status="SUCCESS"
            )
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
        user_id: int,
        ip_address: Optional[str] = None
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

        old_data = {
            "requisition_number": db_requisition.requisition_number,
            "project_id": db_requisition.project_id,
            "supplier_id": db_requisition.supplier_id,
            "total_amount": float(db_requisition.total_amount),
            "status": db_requisition.status,
        }

        update_data = requisition_in.model_dump(exclude_unset=True, exclude={"items", "documents", "retentions"})
        
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

            # Handle retentions update if provided
            if requisition_in.retentions is not None:
                db.query(RequisitionRetention).filter(
                    RequisitionRetention.requisition_id == requisition_id
                ).delete()
                for ret in requisition_in.retentions:
                    db_ret = RequisitionRetention(
                        requisition_id=db_requisition.id,
                        retention_id=ret.retention_id,
                        retention_amount=ret.retention_amount,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    db.add(db_ret)

            db.commit()
            db.refresh(db_requisition)
            AuditLogger.log_action(
                db=db,
                user_id=user_id,
                action="UPDATE",
                module="requisitions",
                description=f"Updated requisition: {db_requisition.requisition_number}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "requisition_number": db_requisition.requisition_number,
                    "project_id": db_requisition.project_id,
                    "supplier_id": db_requisition.supplier_id,
                    "total_amount": float(db_requisition.total_amount),
                    "status": db_requisition.status,
                },
                status="SUCCESS"
            )
            return db_requisition
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if project_id, supplier_id, and user IDs exist."
            )

    def delete(self, db: Session, requisition_id: int, user_id: int = 0, ip_address: Optional[str] = None) -> bool:
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

        req_data = {
            "id": db_requisition.id,
            "requisition_number": db_requisition.requisition_number,
            "project_id": db_requisition.project_id,
            "total_amount": float(db_requisition.total_amount),
            "status": db_requisition.status,
        }

        db.delete(db_requisition)
        db.commit()
        AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action="DELETE",
            module="requisitions",
            description=f"Deleted requisition: {req_data['requisition_number']}",
            ip_address=ip_address,
            old_data=req_data,
            status="SUCCESS"
        )
        return True
    
    def _net_amount(self, req) -> Decimal:
        """Amount effectively committed/spent: total − isr_withheld − iva_withheld − retentions."""
        total = Decimal(str(req.total_amount or 0))
        isr   = Decimal(str(req.isr_withheld_amount or 0))
        iva   = Decimal(str(req.iva_withheld_amount or 0))
        ret   = sum(Decimal(str(r.retention_amount or 0)) for r in (req.retentions or []))
        return total - isr - iva - ret

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

    def submit(self, db: Session, requisition_id: int, user_id: int, ip_address: Optional[str] = None) -> Optional[Requisition]:
        """Submit a draft requisition for approval. Commits the amount in the project."""
        db_requisition = self.get(db, requisition_id)

        if not db_requisition:
            return None

        if db_requisition.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit requisition with status '{db_requisition.status}'"
            )

        self._update_project_budget(db, db_requisition.project_id, self._net_amount(db_requisition), 0)

        db_requisition.status = "submitted"
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()
        db_requisition.requested_by = user_id
        db.commit()
        db.refresh(db_requisition)
        AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action="SUBMIT",
            module="requisitions",
            description=f"Submitted requisition: {db_requisition.requisition_number}",
            ip_address=ip_address,
            new_data={
                "status": "submitted",
                "total_amount": float(db_requisition.total_amount),
                "project_id": db_requisition.project_id,
            },
            status="SUCCESS"
        )

        # Notify approvers (persist notifications + SSE broadcast)
        from app.utils.notify import notify_approvers_sync

        notify_approvers_sync(
            db=db,
            requisition_id=db_requisition.id,
            requisition_number=db_requisition.requisition_number,
            project_id=db_requisition.project_id,
            submitted_by_id=user_id,
        )

        return db_requisition

    def cancel(self, db: Session, requisition_id: int, user_id: int, ip_address: Optional[str] = None) -> Optional[Requisition]:
        """Cancel a draft or submitted requisition. Reverses committed amount if submitted."""
        db_requisition = self.get(db, requisition_id)

        if not db_requisition:
            return None

        if db_requisition.status not in ["draft", "submitted"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel requisition with status '{db_requisition.status}'"
            )

        prev_status = db_requisition.status

        if db_requisition.status == "submitted":
            self._update_project_budget(db, db_requisition.project_id, -self._net_amount(db_requisition), 0)

        db_requisition.status = "cancelled"
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()

        db.commit()
        db.refresh(db_requisition)
        AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action="CANCEL",
            module="requisitions",
            description=f"Cancelled requisition: {db_requisition.requisition_number}",
            ip_address=ip_address,
            old_data={"status": prev_status},
            new_data={"status": "cancelled"},
            status="SUCCESS"
        )
        return db_requisition

    def revert_to_draft(self, db: Session, requisition_id: int, user_id: int) -> Optional[Requisition]:
        """Revert a submitted requisition back to draft. Releases the committed amount from the project."""
        db_requisition = self.get(db, requisition_id)

        if not db_requisition:
            return None

        if db_requisition.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revert requisition with status '{db_requisition.status}' to draft"
            )

        self._update_project_budget(db, db_requisition.project_id, -self._net_amount(db_requisition), 0)

        db_requisition.status = "draft"
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()

        db.commit()
        db.refresh(db_requisition)
        return db_requisition

    def approve(self, db: Session, requisition_id: int, user_id: int, item_account_assignments=None, ip_address: Optional[str] = None) -> Optional[Requisition]:
        """Approve a submitted requisition. Moves amount from commited to spent."""
        db_requisition = self.get(db, requisition_id)

        if not db_requisition:
            return None

        if db_requisition.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve requisition with status '{db_requisition.status}'"
            )

        net = self._net_amount(db_requisition)

        self._update_project_budget(
            db, db_requisition.project_id,
            -net,   # Libera el committed
            net     # Mueve a spent
        )
        
        if db_requisition.currency == "USD":
            from app.utils.banxico import fetch_usd_exchange_rate
            try:
                db_requisition.exchange_rate = fetch_usd_exchange_rate()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"No se pudo obtener el tipo de cambio de Banxico: {exc}",
                )

        db_requisition.status = "approved"
        db_requisition.approved_by = user_id
        db_requisition.approved_at = datetime.now()
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()

        if item_account_assignments:
            valid_item_ids = {item.id for item in db_requisition.items}
            for assignment in item_account_assignments:
                if assignment.item_id not in valid_item_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El item {assignment.item_id} no pertenece a la requisición {requisition_id}"
                    )
            item_map = {item.id: item for item in db_requisition.items}
            for assignment in item_account_assignments:
                item_map[assignment.item_id].account_id = assignment.account_id

        db.commit()
        db.refresh(db_requisition)
        AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action="APPROVE",
            module="requisitions",
            description=f"Approved requisition: {db_requisition.requisition_number}",
            ip_address=ip_address,
            new_data={
                "status": "approved",
                "total_amount": float(db_requisition.total_amount),
            },
            status="SUCCESS"
        )

        # Notify the requester
        from app.utils.notify import notify_requester_sync

        notify_requester_sync(
            db=db,
            requisition_id=db_requisition.id,
            requisition_number=db_requisition.requisition_number,
            project_id=db_requisition.project_id,
            requester_user_id=db_requisition.created_by,
            action="approved",
            acted_by_id=user_id,
        )

        return db_requisition

    def reject(self, db: Session, requisition_id: int, user_id: int, rejection_reason: str, ip_address: Optional[str] = None) -> Optional[Requisition]:
        """Reject a submitted requisition. Releases the committed amount."""
        db_requisition = self.get(db, requisition_id)
        
        if not db_requisition:
            return None
        
        if db_requisition.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject requisition with status '{db_requisition.status}'"
            )

        self._update_project_budget(db, db_requisition.project_id, -self._net_amount(db_requisition), 0)
        
        db_requisition.status = "rejected"
        db_requisition.rejected_by = user_id
        db_requisition.rejected_at = datetime.utcnow()
        db_requisition.rejection_reason = rejection_reason
        db_requisition.updated_by = user_id
        db_requisition.updated_at = func.now()

        db.commit()
        db.refresh(db_requisition)
        AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action="REJECT",
            module="requisitions",
            description=f"Rejected requisition: {db_requisition.requisition_number}. Reason: {rejection_reason}",
            ip_address=ip_address,
            old_data={"status": "submitted"},
            new_data={"status": "rejected", "rejection_reason": rejection_reason},
            status="SUCCESS"
        )

        # Notify the requester
        from app.utils.notify import notify_requester_sync

        notify_requester_sync(
            db=db,
            requisition_id=db_requisition.id,
            requisition_number=db_requisition.requisition_number,
            project_id=db_requisition.project_id,
            requester_user_id=db_requisition.created_by,
            action="rejected",
            acted_by_id=user_id,
            rejection_reason=rejection_reason,
        )

        return db_requisition
    
    def search(
        self,
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        requested_by: Optional[int] = None,
        viewer_id: Optional[int] = None,
    ) -> List[Requisition]:
        """Search requisitions by requisition number, supplier name, project name, or status."""
        pattern = f"%{search_term}%"
        query = (
            db.query(Requisition)
            .join(Supplier, Requisition.supplier_id == Supplier.id, isouter=True)
            .join(Project, Requisition.project_id == Project.id, isouter=True)
            .options(
                joinedload(Requisition.supplier),
                joinedload(Requisition.project),
                joinedload(Requisition.creator),
            )
            .filter(
                Requisition.requisition_number.ilike(pattern)
                | Supplier.name.ilike(pattern)
                | Project.name.ilike(pattern)
                | Requisition.status.ilike(pattern)
            )
        )
        if viewer_id is not None:
            query = query.filter(
                or_(Requisition.requested_by == viewer_id, Requisition.created_by == viewer_id)
            )
        elif requested_by is not None:
            query = query.filter(Requisition.requested_by == requested_by)
        return (
            query
            .order_by(Requisition.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def assign_purchase_order(
        self,
        db: Session,
        requisition_id: int,
        data: RequisitionAssignPurchaseOrder,
        user_id: int,
        ip_address: Optional[str] = None,
    ) -> Optional[Requisition]:
        db_requisition = self.get(db, requisition_id)
        if not db_requisition:
            return None

        old_po = db_requisition.purchase_order
        db_requisition.purchase_order = data.purchase_order
        db_requisition.updated_by = user_id

        AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action="UPDATE",
            module="requisition",
            description=f"Assigned purchase order to requisition {requisition_id}",
            old_data={"purchase_order": old_po},
            new_data={"purchase_order": data.purchase_order},
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(db_requisition)
        return db_requisition

# Create a singleton instance
requisition = CRUDRequisition()
