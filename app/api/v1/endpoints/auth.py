import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user_from_cookie, get_current_user_with_permissions, get_user_permissions
from app.core.security import (
    decode_token,
    delete_access_token_cookie,
    delete_refresh_token_cookie,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_token_from_cookie,
    set_access_token_cookie,
    set_refresh_token_cookie,
    verify_password,
)
from app.crud.password_reset import password_reset as password_reset_crud
from app.crud.system_configuration import system_configuration as system_config_crud
from app.crud.user import user as user_crud
from app.models.user import User
from app.schemas.user import UserWithPermissions, PermissionItem
from app.utils.email import send_email

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseModel):
    """Login response schema."""
    message: str
    access_token: str
    refresh_token: str
    token_type: str
    user: dict
    permissions: list[PermissionItem]


class RefreshResponse(BaseModel):
    """Refresh token response schema."""
    message: str


class LogoutResponse(BaseModel):
    """Logout response schema."""
    message: str


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and set JWT tokens in cookies.
    
    - Accepts username or email
    - Returns user information
    - Sets access_token and refresh_token cookies
    """
    # Try to find user by username or email
    db_user = user_crud.get_by_username(db, username=login_data.username)
    if not db_user:
        db_user = user_crud.get_by_email(db, email=login_data.username)
    
    # Verify user exists and password is correct
    if not db_user or not verify_password(login_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access and refresh tokens
    access_token = create_access_token(data={"sub": db_user.id})
    refresh_token = create_refresh_token(data={"sub": db_user.id})
    
    # Set tokens in cookies
    set_access_token_cookie(response, access_token)
    set_refresh_token_cookie(response, refresh_token)
    
    # Update last login timestamp
    user_crud.update_last_login(db, user_id=db_user.id)
    
    permissions = get_user_permissions(db, db_user.role_id, is_superuser=bool(db_user.is_superuser))
    
    return LoginResponse(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": db_user.id,
            "username": db_user.username,
            "name": db_user.name,
            "email": db_user.email,
            "is_active": db_user.is_active,
            "must_change_password": db_user.must_change_password,
            "role": {
                "id": db_user.role.id,
                "role_code": db_user.role.role_code,
                "name": db_user.role.name
            }
        },
        permissions=permissions
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from cookie.
    
    - Validates refresh token
    - Issues new access token
    - Optionally issues new refresh token (token rotation)
    """
    # Get refresh token from cookie
    refresh_token = get_token_from_cookie(request, settings.REFRESH_COOKIE_NAME)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate refresh token
    payload = decode_token(refresh_token)
    
    # Verify token type
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token (convert from string to int)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists and is active
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": user_id})
    set_access_token_cookie(response, new_access_token)
    
    # Optional: Rotate refresh token (recommended for security)
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    set_refresh_token_cookie(response, new_refresh_token)
    
    return RefreshResponse(message="Token refreshed successfully")


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response):
    """
    Logout user by clearing JWT tokens from cookies.
    
    - Deletes access_token and refresh_token cookies
    """
    delete_access_token_cookie(response)
    delete_refresh_token_cookie(response)
    
    return LogoutResponse(message="Logout successful")


@router.get("/me", response_model=UserWithPermissions)
def get_current_user_info(
    user_with_permissions: UserWithPermissions = Depends(get_current_user_with_permissions),
):
    """
    Get current authenticated user information with all available permissions.

    - Requires valid access token in cookie or Authorization header
    - Returns user details, role, and list of permissions
    """
    return user_with_permissions


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    message: str


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset link.
    Always returns 200 regardless of whether the email exists.
    """
    _GENERIC_MSG = "Si el correo existe en el sistema, recibirás instrucciones para restablecer tu contraseña."

    db_user = user_crud.get_by_email(db, email=body.email)
    if not db_user or not db_user.is_active:
        return MessageResponse(message=_GENERIC_MSG)

    # Invalidate any previous unused tokens
    password_reset_crud.invalidate_user_tokens(db, user_id=db_user.id)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)

    password_reset_crud.create(db, user_id=db_user.id, token_hash=token_hash, expires_at=expires_at)

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
    print(reset_link)
    html_body = f"""
    <p>Recibiste este correo porque solicitaste restablecer tu contraseña.</p>
    <p>Haz clic en el siguiente enlace para continuar (válido por 1 hora):</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>Si no solicitaste esto, puedes ignorar este mensaje.</p>
    """
    smtp_config_record = system_config_crud.get_active(db)
    if smtp_config_record:
        smtp_cfg = {
            "host": smtp_config_record.smtp_host,
            "port": smtp_config_record.smtp_port,
            "username": smtp_config_record.smtp_username,
            "password": smtp_config_record.smtp_password,
            "encryption": smtp_config_record.smtp_encryption,
        }
        print("Intentando enviar correo de recuperación a %s", body.email)
        try:
            send_email(smtp_cfg, body.email, "Restablecer contraseña", html_body)
        except Exception as exc:
            logger.error("Fallo al enviar correo de recuperación: %s", exc)
    else:
        logger.warning("No hay configuración SMTP activa; no se envió correo de recuperación")

    return MessageResponse(message=_GENERIC_MSG)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid, non-expired token.
    """
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    reset_record = password_reset_crud.get_by_token_hash(db, token_hash=token_hash)

    now = datetime.now(tz=timezone.utc)
    if (
        not reset_record
        or reset_record.used
        or reset_record.expires_at.replace(tzinfo=timezone.utc) <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    db_user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    db_user.password_hash = get_password_hash(body.new_password)
    db_user.must_change_password = False
    password_reset_crud.mark_as_used(db, reset_record)
    db.commit()

    return MessageResponse(message="Contraseña actualizada correctamente")


class SetPasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


@router.post("/set-password", response_model=MessageResponse)
def set_password(
    body: SetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Set a new password for the authenticated user (replaces a temporary password).
    Clears must_change_password flag on success.
    """
    user_crud.set_password(
        db,
        db_user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return MessageResponse(message="Contraseña actualizada correctamente")
