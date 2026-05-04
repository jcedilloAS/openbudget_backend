from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status
import bcrypt
from datetime import datetime

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.audit import AuditLogger


class CRUDUser:
    """CRUD operations for User model."""
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def get(self, db: Session, user_id: int) -> Optional[User]:
        """Get a single user by ID with role eager loaded."""
        return db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get a single user by username with role eager loaded."""
        return db.query(User).options(joinedload(User.role)).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a single user by email with role eager loaded."""
        return db.query(User).options(joinedload(User.role)).filter(User.email == email).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        role_id: Optional[int] = None
    ) -> List[User]:
        """Get multiple users with pagination and optional filtering."""
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if role_id is not None:
            query = query.filter(User.role_id == role_id)
        
        return query.offset(skip).limit(limit).all()
    
    def count(
        self, 
        db: Session, 
        is_active: Optional[bool] = None,
        role_id: Optional[int] = None
    ) -> int:
        """Count total users with optional filtering."""
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if role_id is not None:
            query = query.filter(User.role_id == role_id)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        user_in: UserCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> User:
        """Create a new user."""
        # Check if username already exists
        existing_user = self.get_by_username(db, user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_in.username}' already exists"
            )
        
        # Check if email already exists
        existing_email = self.get_by_email(db, user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_in.email}' already exists"
            )
        
        # Hash password
        hashed_password = self.get_password_hash(user_in.password)
        
        db_user = User(
            username=user_in.username,
            name=user_in.name,
            email=user_in.email,
            password_hash=hashed_password,
            role_id=user_in.role_id,
            is_active=user_in.is_active,
            must_change_password=True,
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="users",
                description=f"Created user: {db_user.username}",
                ip_address=ip_address,
                new_data={
                    "id": db_user.id,
                    "username": db_user.username,
                    "name": db_user.name,
                    "email": db_user.email,
                    "role_id": db_user.role_id,
                    "is_active": db_user.is_active
                },
                status="SUCCESS"
            )
            
            return db_user
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="users",
                description=f"Failed to create user: {user_in.username}",
                ip_address=ip_address,
                status="FAILURE"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if role_id exists."
            )
    
    def update(
        self, 
        db: Session, 
        user_id: int, 
        user_in: UserUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """Update an existing user."""
        db_user = self.get(db, user_id)
        
        if not db_user:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_user.id,
            "username": db_user.username,
            "name": db_user.name,
            "email": db_user.email,
            "role_id": db_user.role_id,
            "is_active": db_user.is_active
        }
        
        # Check if new username already exists (if being updated)
        if user_in.username and user_in.username != db_user.username:
            existing_user = self.get_by_username(db, user_in.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{user_in.username}' already exists"
                )
        
        # Check if new email already exists (if being updated)
        if user_in.email and user_in.email != db_user.email:
            existing_email = self.get_by_email(db, user_in.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_in.email}' already exists"
                )
        
        # Update only provided fields
        update_data = user_in.model_dump(exclude_unset=True)
        
        # Handle password separately
        if "password" in update_data:
            password = update_data.pop("password")
            update_data["password_hash"] = self.get_password_hash(password)
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        try:
            db.commit()
            db.refresh(db_user)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="users",
                description=f"Updated user: {db_user.username}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_user.id,
                    "username": db_user.username,
                    "name": db_user.name,
                    "email": db_user.email,
                    "role_id": db_user.role_id,
                    "is_active": db_user.is_active
                },
                status="SUCCESS"
            )
            
            return db_user
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="users",
                description=f"Failed to update user ID: {user_id}",
                ip_address=ip_address,
                status="FAILURE"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if role_id exists."
            )
    
    def update_last_login(self, db: Session, user_id: int) -> Optional[User]:
        """Update the last login timestamp for a user."""
        db_user = self.get(db, user_id)
        
        if not db_user:
            return None
        
        db_user.last_login_at = datetime.now()
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def delete(
        self, 
        db: Session, 
        user_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """Delete a user."""
        db_user = self.get(db, user_id)
        
        if not db_user:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_user.id,
            "username": db_user.username,
            "name": db_user.name,
            "email": db_user.email,
            "role_id": db_user.role_id,
            "is_active": db_user.is_active
        }
        
        db.delete(db_user)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="users",
            description=f"Deleted user: {old_data['username']} (ID: {user_id})",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_user
    
    def soft_delete(
        self, 
        db: Session, 
        user_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """Soft delete a user by setting is_active to False."""
        db_user = self.get(db, user_id)
        
        if not db_user:
            return None
        
        old_status = db_user.is_active
        db_user.is_active = False
        db.commit()
        db.refresh(db_user)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="users",
            description=f"Soft deleted user: {db_user.username} (ID: {user_id})",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_user
    
    def set_password(self, db: Session, db_user: User, current_password: str, new_password: str) -> User:
        """Verify current password then update to new one and clear must_change_password."""
        if not self.verify_password(current_password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta",
            )
        db_user.password_hash = self.get_password_hash(new_password)
        db_user.must_change_password = False
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.get_by_username(db, username)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user


# Create a singleton instance
user = CRUDUser()
