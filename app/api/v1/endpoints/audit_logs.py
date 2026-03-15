from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.audit_log import audit_log
from app.schemas.audit_log import AuditLog, AuditLogCreate, AuditLogList, AuditLogWithUser

router = APIRouter()


@router.get("/", response_model=AuditLogList, summary="List all audit logs")
def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    module: Optional[str] = Query(None, description="Filter by module"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "list"))
):
    """
    Retrieve a list of audit logs with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **user_id**: Optional filter by user ID
    - **action**: Optional filter by action type (CREATE, UPDATE, DELETE, etc.)
    - **module**: Optional filter by module name
    - **status**: Optional filter by status (SUCCESS, FAILURE)
    - **start_date**: Optional filter from date
    - **end_date**: Optional filter to date
    """
    audit_logs = audit_log.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        user_id=user_id,
        action=action,
        module=module,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    total = audit_log.count(
        db,
        user_id=user_id,
        action=action,
        module=module,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    return AuditLogList(total=total, items=audit_logs)


@router.get("/{audit_log_id}", response_model=AuditLogWithUser, summary="Get audit log by ID")
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "list"))
):
    """
    Retrieve a specific audit log by ID.
    
    - **audit_log_id**: The ID of the audit log to retrieve
    """
    db_audit_log = audit_log.get(db, audit_log_id=audit_log_id)
    
    if not db_audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with id {audit_log_id} not found"
        )
    
    return db_audit_log


@router.post("/", response_model=AuditLog, status_code=status.HTTP_201_CREATED, summary="Create new audit log")
def create_audit_log(
    audit_log_in: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "create"))
):
    """
    Create a new audit log entry.
    
    - **user_id**: User ID who performed the action (required)
    - **action**: Action performed (required)
    - **module**: Module/table affected (required)
    - **description**: Detailed description (optional)
    - **ip_address**: IP address of the user (optional)
    - **status**: Status of the action (required)
    - **old_data**: Previous data state (optional)
    - **new_data**: New data state (optional)
    """
    return audit_log.create(db, audit_log_in=audit_log_in)


@router.get("/user/{user_id}", response_model=AuditLogList, summary="Get audit logs by user")
def get_audit_logs_by_user(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "list"))
):
    """
    Retrieve all audit logs for a specific user.
    
    - **user_id**: The ID of the user
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    audit_logs = audit_log.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    total = audit_log.count(db, user_id=user_id)
    
    return AuditLogList(total=total, items=audit_logs)


@router.get("/module/{module}", response_model=AuditLogList, summary="Get audit logs by module")
def get_audit_logs_by_module(
    module: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "list"))
):
    """
    Retrieve all audit logs for a specific module.
    
    - **module**: The name of the module
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    audit_logs = audit_log.get_by_module(db, module=module, skip=skip, limit=limit)
    total = audit_log.count(db, module=module)
    
    return AuditLogList(total=total, items=audit_logs)


@router.get("/recent/last-hours", response_model=list[AuditLog], summary="Get recent audit logs")
def get_recent_audit_logs(
    hours: int = Query(24, ge=1, le=720, description="Number of hours to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "list"))
):
    """
    Retrieve recent audit logs within the specified hours.
    
    - **hours**: Number of hours to look back (default: 24, max: 720/30 days)
    - **limit**: Maximum number of records to return
    """
    return audit_log.get_recent(db, hours=hours, limit=limit)


@router.delete("/cleanup", summary="Delete old audit logs")
def cleanup_old_logs(
    days: int = Query(90, ge=30, le=365, description="Delete logs older than this many days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit_logs", "delete"))
):
    """
    Delete audit logs older than specified days.
    
    - **days**: Delete logs older than this many days (default: 90, min: 30, max: 365)
    """
    deleted_count = audit_log.delete_old_logs(db, days=days)
    
    return {
        "message": f"Successfully deleted {deleted_count} old audit log entries",
        "deleted_count": deleted_count,
        "older_than_days": days
    }
