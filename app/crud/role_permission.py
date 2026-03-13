from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.role_permission import RolePermission
from app.models.role import Role
from app.models.catalog_action import CatalogAction
from app.models.catalog import Catalog
from app.models.action import Action
from app.schemas.role_permission import RolePermissionCreate, RolePermissionUpdate, RolePermissionWithDetails, RolePermissionBulkCreate
from app.utils.audit import AuditLogger


class CRUDRolePermission:
    """CRUD operations for RolePermission model."""
    
    def get(self, db: Session, role_permission_id: int) -> Optional[RolePermission]:
        """Get a single role permission by ID."""
        return db.query(RolePermission).filter(RolePermission.id == role_permission_id).first()
    
    def get_by_role_and_catalog_action(
        self, 
        db: Session, 
        role_id: int, 
        catalog_action_id: int
    ) -> Optional[RolePermission]:
        """Get a role permission by role_id and catalog_action_id."""
        return db.query(RolePermission).filter(
            and_(
                RolePermission.role_id == role_id,
                RolePermission.catalog_action_id == catalog_action_id
            )
        ).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        role_id: Optional[int] = None,
        catalog_action_id: Optional[int] = None,
        is_allowed: Optional[bool] = None
    ) -> List[RolePermission]:
        """Get multiple role permissions with pagination and optional filtering."""
        query = db.query(RolePermission)
        
        if role_id is not None:
            query = query.filter(RolePermission.role_id == role_id)
        
        if catalog_action_id is not None:
            query = query.filter(RolePermission.catalog_action_id == catalog_action_id)
        
        if is_allowed is not None:
            query = query.filter(RolePermission.is_allowed == is_allowed)
        
        return query.offset(skip).limit(limit).all()
    
    def get_multi_with_details(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        role_id: Optional[int] = None,
        catalog_action_id: Optional[int] = None,
        is_allowed: Optional[bool] = None
    ) -> List[RolePermissionWithDetails]:
        """Get multiple role permissions with role, catalog and action details."""
        query = db.query(
            RolePermission.id,
            RolePermission.role_id,
            RolePermission.catalog_action_id,
            RolePermission.is_allowed,
            RolePermission.created_at,
            RolePermission.updated_at,
            Role.role_code,
            Role.name.label('role_name'),
            Catalog.catalog_code,
            Catalog.catalog_name,
            Action.action_code,
            Action.action_name
        ).join(
            Role, RolePermission.role_id == Role.id
        ).join(
            CatalogAction, RolePermission.catalog_action_id == CatalogAction.id
        ).join(
            Catalog, CatalogAction.catalog_id == Catalog.id
        ).join(
            Action, CatalogAction.action_id == Action.id
        )
        
        if role_id is not None:
            query = query.filter(RolePermission.role_id == role_id)
        
        if catalog_action_id is not None:
            query = query.filter(RolePermission.catalog_action_id == catalog_action_id)
        
        if is_allowed is not None:
            query = query.filter(RolePermission.is_allowed == is_allowed)
        
        results = query.offset(skip).limit(limit).all()
        
        return [
            RolePermissionWithDetails(
                id=r.id,
                role_id=r.role_id,
                catalog_action_id=r.catalog_action_id,
                is_allowed=r.is_allowed,
                created_at=r.created_at,
                updated_at=r.updated_at,
                role_code=r.role_code,
                role_name=r.role_name,
                catalog_code=r.catalog_code,
                catalog_name=r.catalog_name,
                action_code=r.action_code,
                action_name=r.action_name
            )
            for r in results
        ]
    
    def count(
        self, 
        db: Session, 
        role_id: Optional[int] = None,
        catalog_action_id: Optional[int] = None,
        is_allowed: Optional[bool] = None
    ) -> int:
        """Count total role permissions with optional filtering."""
        query = db.query(RolePermission)
        
        if role_id is not None:
            query = query.filter(RolePermission.role_id == role_id)
        
        if catalog_action_id is not None:
            query = query.filter(RolePermission.catalog_action_id == catalog_action_id)
        
        if is_allowed is not None:
            query = query.filter(RolePermission.is_allowed == is_allowed)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        role_permission_in: RolePermissionCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> RolePermission:
        """Create a new role permission."""
        # Check if permission already exists
        existing = self.get_by_role_and_catalog_action(
            db, 
            role_permission_in.role_id, 
            role_permission_in.catalog_action_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission for role {role_permission_in.role_id} and catalog_action {role_permission_in.catalog_action_id} already exists"
            )
        
        # Verify role exists
        role = db.query(Role).filter(Role.id == role_permission_in.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_permission_in.role_id} not found"
            )
        
        # Verify catalog_action exists
        catalog_action = db.query(CatalogAction).filter(CatalogAction.id == role_permission_in.catalog_action_id).first()
        if not catalog_action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CatalogAction with id {role_permission_in.catalog_action_id} not found"
            )
        
        db_role_permission = RolePermission(
            role_id=role_permission_in.role_id,
            catalog_action_id=role_permission_in.catalog_action_id,
            is_allowed=role_permission_in.is_allowed
        )
        
        try:
            db.add(db_role_permission)
            db.commit()
            db.refresh(db_role_permission)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="role_permissions",
                description=f"Created role permission: role_id={db_role_permission.role_id}, catalog_action_id={db_role_permission.catalog_action_id}",
                ip_address=ip_address,
                new_data={
                    "id": db_role_permission.id,
                    "role_id": db_role_permission.role_id,
                    "catalog_action_id": db_role_permission.catalog_action_id,
                    "is_allowed": db_role_permission.is_allowed
                },
                status="SUCCESS"
            )
            
            return db_role_permission
            
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="role_permissions",
                description=f"Failed to create role permission",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating role permission: {str(e)}"
            )
    
    def bulk_create(
        self,
        db: Session,
        bulk_data: RolePermissionBulkCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> List[RolePermission]:
        """Bulk create role permissions."""
        # Verify role exists
        role = db.query(Role).filter(Role.id == bulk_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {bulk_data.role_id} not found"
            )
        
        created_permissions = []
        errors = []
        
        for catalog_action_id in bulk_data.catalog_action_ids:
            # Check if permission already exists
            existing = self.get_by_role_and_catalog_action(db, bulk_data.role_id, catalog_action_id)
            if existing:
                errors.append(f"Permission for catalog_action {catalog_action_id} already exists")
                continue
            
            # Verify catalog_action exists
            catalog_action = db.query(CatalogAction).filter(CatalogAction.id == catalog_action_id).first()
            if not catalog_action:
                errors.append(f"CatalogAction with id {catalog_action_id} not found")
                continue
            
            db_role_permission = RolePermission(
                role_id=bulk_data.role_id,
                catalog_action_id=catalog_action_id,
                is_allowed=bulk_data.is_allowed
            )
            
            try:
                db.add(db_role_permission)
                db.flush()
                created_permissions.append(db_role_permission)
            except IntegrityError as e:
                errors.append(f"Error creating permission for catalog_action {catalog_action_id}: {str(e)}")
                continue
        
        if created_permissions:
            db.commit()
            for perm in created_permissions:
                db.refresh(perm)
            
            # Log the bulk create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="BULK_CREATE",
                module="role_permissions",
                description=f"Bulk created {len(created_permissions)} permissions for role {bulk_data.role_id}",
                ip_address=ip_address,
                new_data={
                    "role_id": bulk_data.role_id,
                    "created_count": len(created_permissions),
                    "catalog_action_ids": [p.catalog_action_id for p in created_permissions]
                },
                status="SUCCESS"
            )
        
        if errors and not created_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create any permissions: {', '.join(errors)}"
            )
        
        return created_permissions
    
    def update(
        self,
        db: Session,
        role_permission_id: int,
        role_permission_in: RolePermissionUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[RolePermission]:
        """Update an existing role permission."""
        db_role_permission = self.get(db, role_permission_id)
        
        if not db_role_permission:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_role_permission.id,
            "role_id": db_role_permission.role_id,
            "catalog_action_id": db_role_permission.catalog_action_id,
            "is_allowed": db_role_permission.is_allowed
        }
        
        # Update only provided fields
        update_data = role_permission_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_role_permission, field, value)
        
        try:
            db.commit()
            db.refresh(db_role_permission)
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="role_permissions",
                description=f"Updated role permission ID: {role_permission_id}",
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_role_permission.id,
                    "role_id": db_role_permission.role_id,
                    "catalog_action_id": db_role_permission.catalog_action_id,
                    "is_allowed": db_role_permission.is_allowed
                },
                status="SUCCESS"
            )
            
            return db_role_permission
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="role_permissions",
                description=f"Failed to update role permission ID: {role_permission_id}",
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
        role_permission_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[RolePermission]:
        """Delete a role permission."""
        db_role_permission = self.get(db, role_permission_id)
        
        if not db_role_permission:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_role_permission.id,
            "role_id": db_role_permission.role_id,
            "catalog_action_id": db_role_permission.catalog_action_id,
            "is_allowed": db_role_permission.is_allowed
        }
        
        db.delete(db_role_permission)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="role_permissions",
            description=f"Deleted role permission ID: {role_permission_id}",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_role_permission


# Create a singleton instance
role_permission = CRUDRolePermission()
