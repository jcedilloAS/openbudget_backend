"""Audit logging utilities for tracking database operations."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.schemas.audit_log import AuditLogCreate
from app.utils.request import get_client_ip


class AuditLogger:
    """Utility class for logging database operations."""
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        module: str,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS"
    ):
        """
        Log an audit entry.
        
        Args:
            db: Database session
            user_id: ID of the user performing the action
            action: Action performed (CREATE, UPDATE, DELETE, etc.)
            module: Module/table affected
            description: Detailed description of the action
            ip_address: IP address of the user
            old_data: Previous data state (for updates/deletes)
            new_data: New data state (for creates/updates)
            status: Status of the action (SUCCESS, FAILURE, etc.)
        """
        try:
            # Import here to avoid circular imports
            from app.crud.audit_log import audit_log
            
            audit_log_in = AuditLogCreate(
                user_id=user_id,
                action=action,
                module=module,
                description=description,
                ip_address=ip_address,
                status=status,
                old_data=old_data,
                new_data=new_data
            )
            audit_log.create(db, audit_log_in=audit_log_in)
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"[AUDIT LOG ERROR] Failed to log action: {str(e)}")
    
    @staticmethod
    def log_from_request(
        db: Session,
        request: Request,
        user_id: int,
        action: str,
        module: str,
        description: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS"
    ):
        """
        Log an audit entry extracting IP from request automatically.
        
        Convenience method that extracts IP address from request.
        
        Args:
            db: Database session
            request: FastAPI Request object
            user_id: ID of the user performing the action
            action: Action performed (CREATE, UPDATE, DELETE, etc.)
            module: Module/table affected
            description: Detailed description of the action
            old_data: Previous data state (for updates/deletes)
            new_data: New data state (for creates/updates)
            status: Status of the action (SUCCESS, FAILURE, etc.)
        """
        ip_address = get_client_ip(request)
        return AuditLogger.log_action(
            db=db,
            user_id=user_id,
            action=action,
            module=module,
            description=description,
            ip_address=ip_address,
            old_data=old_data,
            new_data=new_data,
            status=status
        )
