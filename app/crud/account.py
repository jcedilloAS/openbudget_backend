from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple
from fastapi import HTTPException, status

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountBulkUploadResult, AccountBulkUploadError
from app.utils.audit import AuditLogger


class CRUDAccount:
    """CRUD operations for Account model."""
    
    def get(self, db: Session, account_id: int) -> Optional[Account]:
        """Get a single account by ID."""
        return db.query(Account).filter(Account.id == account_id).first()
    
    def get_by_account_number(self, db: Session, account_number: str) -> Optional[Account]:
        """Get a single account by account number."""
        return db.query(Account).filter(Account.account_number == account_number).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Account]:
        """Get multiple accounts with pagination and optional filtering."""
        query = db.query(Account)
        
        if is_active is not None:
            query = query.filter(Account.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """Count total accounts with optional filtering."""
        query = db.query(Account)
        
        if is_active is not None:
            query = query.filter(Account.is_active == is_active)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        account_in: AccountCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Account:
        """Create a new account."""
        # Check if account number already exists
        existing_account = self.get_by_account_number(db, account_in.account_number)
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account with number '{account_in.account_number}' already exists"
            )
        
        db_account = Account(
            account_number=account_in.account_number,
            description=account_in.description,
            is_active=account_in.is_active
        )
        
        try:
            db.add(db_account)
            db.commit()
            db.refresh(db_account)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="accounts",
                description=f"Created account: {db_account.account_number}",
                ip_address=ip_address,
                new_data={
                    "id": db_account.id,
                    "account_number": db_account.account_number,
                    "description": db_account.description,
                    "is_active": db_account.is_active
                },
                status="SUCCESS"
            )
            
            return db_account
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="accounts",
                description=f"Failed to create account: {account_in.account_number}",
                ip_address=ip_address,
                status="FAILURE"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred"
            )
    
    def update(
        self, 
        db: Session, 
        account_id: int, 
        account_in: AccountUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Account]:
        """Update an existing account."""
        db_account = self.get(db, account_id)
        
        if not db_account:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_account.id,
            "account_number": db_account.account_number,
            "description": db_account.description,
            "is_active": db_account.is_active
        }
        
        # Check if new account number already exists (if being updated)
        if account_in.account_number and account_in.account_number != db_account.account_number:
            existing_account = self.get_by_account_number(db, account_in.account_number)
            if existing_account:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Account with number '{account_in.account_number}' already exists"
                )
        
        # Update only provided fields
        update_data = account_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_account, field, value)
        
        try:
            db.commit()
            db.refresh(db_account)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="accounts",
                description=f"Updated account: {db_account.account_number}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_account.id,
                    "account_number": db_account.account_number,
                    "description": db_account.description,
                    "is_active": db_account.is_active
                },
                status="SUCCESS"
            )
            
            return db_account
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="accounts",
                description=f"Failed to update account ID: {account_id}",
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
        account_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Account]:
        """Delete an account."""
        db_account = self.get(db, account_id)
        
        if not db_account:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_account.id,
            "account_number": db_account.account_number,
            "description": db_account.description,
            "is_active": db_account.is_active
        }
        
        db.delete(db_account)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="accounts",
            description=f"Deleted account: {old_data['account_number']} (ID: {account_id})",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_account
    
    def soft_delete(
        self, 
        db: Session, 
        account_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Account]:
        """Soft delete an account by setting is_active to False."""
        db_account = self.get(db, account_id)
        
        if not db_account:
            return None
        
        old_status = db_account.is_active
        db_account.is_active = False
        db.commit()
        db.refresh(db_account)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="accounts",
            description=f"Soft deleted account: {db_account.account_number} (ID: {account_id})",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_account

    def bulk_create(
        self,
        db: Session,
        rows: List[tuple],
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> AccountBulkUploadResult:
        """Bulk create accounts from a list of rows. Col 0 = account_number, Col 1 = description."""
        from app.schemas.account import AccountBulkUploadError
        created, failed = 0, 0
        errors: List[AccountBulkUploadError] = []

        for row_idx, row in enumerate(rows, start=2):  # start=2: row 1 is header
            account_number = str(row[0] or "").strip() if len(row) > 0 else ""
            description = str(row[1] or "").strip() if len(row) > 1 else None

            if not account_number:
                failed += 1
                errors.append(AccountBulkUploadError(
                    row=row_idx,
                    account_number=None,
                    error="account_number is required"
                ))
                continue

            try:
                account_in = AccountCreate(
                    account_number=account_number,
                    description=description or None
                )
                self.create(db, account_in=account_in, current_user_id=current_user_id, ip_address=ip_address)
                created += 1
            except HTTPException as e:
                failed += 1
                errors.append(AccountBulkUploadError(
                    row=row_idx,
                    account_number=account_number,
                    error=e.detail
                ))
            except Exception as e:
                failed += 1
                errors.append(AccountBulkUploadError(
                    row=row_idx,
                    account_number=account_number,
                    error=str(e)
                ))

        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="BULK_CREATE",
            module="accounts",
            description=f"Bulk upload: {created} created, {failed} failed",
            ip_address=ip_address,
            new_data={"created": created, "failed": failed},
            status="SUCCESS" if failed == 0 else "PARTIAL"
        )

        return AccountBulkUploadResult(
            total_rows=created + failed,
            created=created,
            failed=failed,
            errors=errors
        )


# Create a singleton instance
account = CRUDAccount()
