from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.system_configuration import system_configuration
from app.schemas.system_configuration import (
    SystemConfiguration,
    SystemConfigurationCreate,
    SystemConfigurationUpdate,
    SystemConfigurationWithPassword
)
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=SystemConfiguration, summary="Get system configuration")
def get_system_configuration(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("system_configuration", "read"))
):
    """
    Retrieve the active system configuration.
    
    Returns the system-wide configuration settings (excludes sensitive data like SMTP password).
    """
    config = system_configuration.get_active(db)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )
    
    return config


@router.get("/with-password", response_model=SystemConfigurationWithPassword, summary="Get system configuration with password")
def get_system_configuration_with_password(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("system_configuration", "read"))
):
    """
    Retrieve the active system configuration including sensitive data.
    
    **Note**: This endpoint includes the SMTP password (masked). 
    Typically restricted to admin users only.
    """
    config = system_configuration.get_active(db)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )
    
    # Mask the password for security (show only first/last chars)
    if config.smtp_password:
        pwd_len = len(config.smtp_password)
        if pwd_len > 4:
            masked = config.smtp_password[0:2] + "*" * (pwd_len - 4) + config.smtp_password[-2:]
        else:
            masked = "*" * pwd_len
        
        # Create a copy with masked password
        config_dict = {
            "id": config.id,
            "company_name": config.company_name,
            "rfc": config.rfc,
            "smtp_host": config.smtp_host,
            "smtp_port": config.smtp_port,
            "smtp_username": config.smtp_username,
            "smtp_password": masked,
            "smtp_encryption": config.smtp_encryption,
            "created_at": config.created_at,
            "created_by": config.created_by,
            "updated_at": config.updated_at,
            "updated_by": config.updated_by
        }
        return config_dict
    
    return config


@router.get("/{config_id}", response_model=SystemConfiguration, summary="Get system configuration by ID")
def get_configuration_by_id(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("system_configuration", "read"))
):
    """
    Retrieve a specific system configuration by ID.
    
    - **config_id**: The ID of the configuration to retrieve
    """
    config = system_configuration.get(db, config_id=config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System configuration with id {config_id} not found"
        )
    
    return config


@router.post("/", response_model=SystemConfiguration, summary="Create or update system configuration")
def create_or_update_system_configuration(
    config_in: SystemConfigurationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("system_configuration", "create"))
):
    """
    Create or update the system configuration (upsert).
    
    **Note**: Only one configuration record exists. If it doesn't exist, it will be created.
    If it already exists, it will be updated with the provided values.
    
    - **company_name**: Company name
    - **rfc**: RFC (Tax ID)
    - **smtp_host**: SMTP server host
    - **smtp_port**: SMTP server port
    - **smtp_username**: SMTP username
    - **smtp_password**: SMTP password
    - **smtp_encryption**: SMTP encryption type (TLS, SSL, None)
    """
    ip_address = get_client_ip(request)
    return system_configuration.create_or_update(
        db,
        config_in=config_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{config_id}", response_model=SystemConfiguration, summary="Update system configuration")
def update_system_configuration(
    config_id: int,
    config_in: SystemConfigurationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("system_configuration", "update"))
):
    """
    Update an existing system configuration.
    
    - **config_id**: The ID of the configuration to update
    - **company_name**: New company name (optional)
    - **rfc**: New RFC (optional)
    - **smtp_host**: New SMTP host (optional)
    - **smtp_port**: New SMTP port (optional)
    - **smtp_username**: New SMTP username (optional)
    - **smtp_password**: New SMTP password (optional, omit if not changing)
    - **smtp_encryption**: New SMTP encryption type (optional)
    """
    ip_address = get_client_ip(request)
    db_config = system_configuration.update(
        db,
        config_id=config_id,
        config_in=config_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System configuration with id {config_id} not found"
        )
    
    return db_config
