from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from fastapi import HTTPException, status

from app.models.system_configuration import SystemConfiguration
from app.schemas.system_configuration import SystemConfigurationCreate, SystemConfigurationUpdate
from app.utils.audit import AuditLogger


class CRUDSystemConfiguration:
    """CRUD operations for SystemConfiguration model."""
    
    def get(self, db: Session, config_id: int) -> Optional[SystemConfiguration]:
        """Get a single system configuration by ID."""
        return db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
    
    def get_active(self, db: Session) -> Optional[SystemConfiguration]:
        """Get the active system configuration (should be only one record)."""
        return db.query(SystemConfiguration).first()
    
    def create_or_update(
        self, 
        db: Session, 
        config_in: SystemConfigurationCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> SystemConfiguration:
        """Create a new system configuration or update if already exists (upsert)."""
        
        # Check if configuration already exists (should be singleton)
        existing_config = self.get_active(db)
        
        if existing_config:
            # Update existing configuration
            try:
                # Track changes for audit
                changes = []
                fields_to_update = {
                    'company_name': config_in.company_name,
                    'rfc': config_in.rfc,
                    'smtp_host': config_in.smtp_host,
                    'smtp_port': config_in.smtp_port,
                    'smtp_username': config_in.smtp_username,
                    'smtp_password': config_in.smtp_password,
                    'smtp_encryption': config_in.smtp_encryption
                }
                
                for field, value in fields_to_update.items():
                    old_value = getattr(existing_config, field)
                    if old_value != value:
                        # Mask password in audit log
                        display_value = "***" if field == "smtp_password" else value
                        changes.append(f"{field}: {old_value} -> {display_value}")
                        setattr(existing_config, field, value)
                
                existing_config.updated_by = current_user_id
                
                db.commit()
                db.refresh(existing_config)
                
                # Audit log
                if changes:
                    AuditLogger.log_action(
                        db=db,
                        user_id=current_user_id,
                        action="UPDATE",
                        table_name="system_configuration",
                        record_id=existing_config.id,
                        ip_address=ip_address or "unknown",
                        details=f"Updated system configuration: {', '.join(changes)}"
                    )
                
                return existing_config
                
            except IntegrityError as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database integrity error: {str(e)}"
                )
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error updating system configuration: {str(e)}"
                )
        
        # Create new configuration
        try:
            db_config = SystemConfiguration(
                company_name=config_in.company_name,
                rfc=config_in.rfc,
                smtp_host=config_in.smtp_host,
                smtp_port=config_in.smtp_port,
                smtp_username=config_in.smtp_username,
                smtp_password=config_in.smtp_password,
                smtp_encryption=config_in.smtp_encryption,
                created_by=current_user_id,
                updated_by=current_user_id
            )
            
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            
            # Audit log
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                table_name="system_configuration",
                record_id=db_config.id,
                ip_address=ip_address or "unknown",
                details=f"Created system configuration"
            )
            
            return db_config
            
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating system configuration: {str(e)}"
            )
    
    def update(
        self, 
        db: Session, 
        config_id: int, 
        config_in: SystemConfigurationUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[SystemConfiguration]:
        """Update an existing system configuration."""
        db_config = self.get(db, config_id=config_id)
        
        if not db_config:
            return None
        
        update_data = config_in.model_dump(exclude_unset=True)
        
        if not update_data:
            return db_config
        
        try:
            # Track changes for audit
            changes = []
            for field, value in update_data.items():
                if hasattr(db_config, field):
                    old_value = getattr(db_config, field)
                    if old_value != value:
                        # Mask password in audit log
                        display_value = "***" if field == "smtp_password" else value
                        changes.append(f"{field}: {old_value} -> {display_value}")
                        setattr(db_config, field, value)
            
            db_config.updated_by = current_user_id
            
            db.commit()
            db.refresh(db_config)
            
            # Audit log
            if changes:
                AuditLogger.log_action(
                    db=db,
                    user_id=current_user_id,
                    action="UPDATE",
                    table_name="system_configuration",
                    record_id=db_config.id,
                    ip_address=ip_address or "unknown",
                    details=f"Updated system configuration: {', '.join(changes)}"
                )
            
            return db_config
            
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating system configuration: {str(e)}"
            )


# Create instance
system_configuration = CRUDSystemConfiguration()
