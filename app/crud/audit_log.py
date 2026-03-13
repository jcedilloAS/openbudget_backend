from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


class CRUDAuditLog:
    """CRUD operations for AuditLog model."""
    
    def get(self, db: Session, audit_log_id: int) -> Optional[AuditLog]:
        """Get a single audit log by ID."""
        return db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        module: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get multiple audit logs with pagination and optional filtering."""
        query = db.query(AuditLog)
        
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action is not None:
            query = query.filter(AuditLog.action == action)
        
        if module is not None:
            query = query.filter(AuditLog.module == module)
        
        if status is not None:
            query = query.filter(AuditLog.status == status)
        
        if start_date is not None:
            query = query.filter(AuditLog.date >= start_date)
        
        if end_date is not None:
            query = query.filter(AuditLog.date <= end_date)
        
        # Order by date descending (most recent first)
        query = query.order_by(desc(AuditLog.date))
        
        return query.offset(skip).limit(limit).all()
    
    def count(
        self, 
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        module: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count total audit logs with optional filtering."""
        query = db.query(AuditLog)
        
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action is not None:
            query = query.filter(AuditLog.action == action)
        
        if module is not None:
            query = query.filter(AuditLog.module == module)
        
        if status is not None:
            query = query.filter(AuditLog.status == status)
        
        if start_date is not None:
            query = query.filter(AuditLog.date >= start_date)
        
        if end_date is not None:
            query = query.filter(AuditLog.date <= end_date)
        
        return query.count()
    
    def create(self, db: Session, audit_log_in: AuditLogCreate) -> AuditLog:
        """Create a new audit log entry."""
        db_audit_log = AuditLog(
            user_id=audit_log_in.user_id,
            action=audit_log_in.action,
            module=audit_log_in.module,
            description=audit_log_in.description,
            ip_address=audit_log_in.ip_address,
            status=audit_log_in.status,
            old_data=audit_log_in.old_data,
            new_data=audit_log_in.new_data
        )
        
        try:
            db.add(db_audit_log)
            db.commit()
            db.refresh(db_audit_log)
            return db_audit_log
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if user_id exists."
            )
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs for a specific user."""
        return db.query(AuditLog)\
            .filter(AuditLog.user_id == user_id)\
            .order_by(desc(AuditLog.date))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_recent(
        self, 
        db: Session, 
        hours: int = 24, 
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent audit logs within the specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return db.query(AuditLog)\
            .filter(AuditLog.date >= cutoff_time)\
            .order_by(desc(AuditLog.date))\
            .limit(limit)\
            .all()
    
    def get_by_module(
        self, 
        db: Session, 
        module: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs for a specific module."""
        return db.query(AuditLog)\
            .filter(AuditLog.module == module)\
            .order_by(desc(AuditLog.date))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def delete_old_logs(self, db: Session, days: int = 90) -> int:
        """Delete audit logs older than specified days. Returns count of deleted records."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(AuditLog)\
            .filter(AuditLog.date < cutoff_date)\
            .delete()
        db.commit()
        return deleted_count


# Create a singleton instance
audit_log = CRUDAuditLog()
