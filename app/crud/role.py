from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.catalog_action import CatalogAction
from app.models.catalog import Catalog
from app.models.action import Action
from app.schemas.role import RoleCreate, RoleUpdate
from app.utils.audit import AuditLogger


class CRUDRole:
    """CRUD operations for Role model."""
    
    def get(self, db: Session, role_id: int) -> Optional[Role]:
        """Get a single role by ID."""
        return db.query(Role).filter(Role.id == role_id).first()
    
    def get_with_permissions(self, db: Session, role_id: int) -> Optional[dict]:
        """Get a single role by ID with its permissions including catalog and action details."""
        db_role = db.query(Role).filter(Role.id == role_id).first()
        if not db_role:
            return None
        
        # Get all permissions for this role with catalog and action details
        permissions_query = db.query(
            RolePermission.catalog_action_id,
            CatalogAction.catalog_id,
            Catalog.catalog_name,
            Catalog.catalog_code,
            CatalogAction.action_id,
            Action.action_name,
            Action.action_code
        ).join(
            CatalogAction, RolePermission.catalog_action_id == CatalogAction.id
        ).join(
            Catalog, CatalogAction.catalog_id == Catalog.id
        ).join(
            Action, CatalogAction.action_id == Action.id
        ).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_allowed == True
        ).all()
        
        # Build permissions list with full details
        permissions_list = [
            {
                "catalog_action_id": p.catalog_action_id,
                "catalog_id": p.catalog_id,
                "catalog_name": p.catalog_name,
                "catalog_code": p.catalog_code,
                "action_id": p.action_id,
                "action_name": p.action_name,
                "action_code": p.action_code
            }
            for p in permissions_query
        ]
        
        # Convert to dict with permissions list
        role_dict = {
            "id": db_role.id,
            "role_code": db_role.role_code,
            "name": db_role.name,
            "description": db_role.description,
            "is_active": db_role.is_active,
            "created_at": db_role.created_at,
            "permissions": permissions_list
        }
        
        return role_dict
    
    def get_by_role_code(self, db: Session, role_code: str) -> Optional[Role]:
        """Get a single role by role code."""
        return db.query(Role).filter(Role.role_code == role_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Role]:
        """Get multiple roles with pagination and optional filtering."""
        query = db.query(Role)
        
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session, is_active: Optional[bool] = None) -> int:
        """Count total roles with optional filtering."""
        query = db.query(Role)
        
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        role_in: RoleCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Role:
        """Create a new role with optional permissions."""
        # Check if role code already exists
        existing_role = self.get_by_role_code(db, role_in.role_code)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with code '{role_in.role_code}' already exists"
            )
        
        # Extract catalog_action_ids before creating the role
        catalog_action_ids = role_in.catalog_action_ids if role_in.catalog_action_ids else []
        
        # Create the role object (without catalog_action_ids)
        db_role = Role(
            role_code=role_in.role_code,
            name=role_in.name,
            description=role_in.description,
            is_active=role_in.is_active
        )
        
        try:
            db.add(db_role)
            db.commit()
            db.refresh(db_role)
            
            # Create role_permissions if catalog_action_ids were provided
            created_permissions = []
            if catalog_action_ids:
                for catalog_action_id in catalog_action_ids:
                    # Verify catalog_action exists
                    catalog_action = db.query(CatalogAction).filter(
                        CatalogAction.id == catalog_action_id
                    ).first()
                    
                    if not catalog_action:
                        continue  # Skip if catalog_action doesn't exist
                    
                    # Check if permission already exists
                    existing_permission = db.query(RolePermission).filter(
                        RolePermission.role_id == db_role.id,
                        RolePermission.catalog_action_id == catalog_action_id
                    ).first()
                    
                    if existing_permission:
                        continue  # Skip if permission already exists
                    
                    # Create the permission
                    db_permission = RolePermission(
                        role_id=db_role.id,
                        catalog_action_id=catalog_action_id,
                        is_allowed=True
                    )
                    db.add(db_permission)
                    created_permissions.append(catalog_action_id)
                
                if created_permissions:
                    db.commit()
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="roles",
                description=f"Created role: {db_role.role_code} with {len(created_permissions)} permissions",
                ip_address=ip_address,
                new_data={
                    "id": db_role.id,
                    "role_code": db_role.role_code,
                    "name": db_role.name,
                    "description": db_role.description,
                    "is_active": db_role.is_active,
                    "permissions_created": created_permissions
                },
                status="SUCCESS"
            )
            
            return db_role
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="roles",
                description=f"Failed to create role: {role_in.role_code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred"
            )
    
    def update(
        self, 
        db: Session, 
        role_id: int, 
        role_in: RoleUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Role]:
        """Update an existing role and optionally update permissions."""
        db_role = self.get(db, role_id)
        
        if not db_role:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_role.id,
            "role_code": db_role.role_code,
            "name": db_role.name,
            "description": db_role.description,
            "is_active": db_role.is_active
        }
        
        # Check if new role code already exists (if being updated)
        if role_in.role_code and role_in.role_code != db_role.role_code:
            existing_role = self.get_by_role_code(db, role_in.role_code)
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with code '{role_in.role_code}' already exists"
                )
        
        # Extract catalog_action_ids before updating
        catalog_action_ids = role_in.catalog_action_ids if hasattr(role_in, 'catalog_action_ids') and role_in.catalog_action_ids is not None else None
        
        # Update only provided fields (exclude catalog_action_ids from model update)
        update_data = role_in.model_dump(exclude_unset=True, exclude={'catalog_action_ids'})
        
        for field, value in update_data.items():
            setattr(db_role, field, value)
        
        try:
            db.commit()
            db.refresh(db_role)
            
            # Update permissions if catalog_action_ids were provided
            permissions_updated = False
            if catalog_action_ids is not None:
                # Delete existing permissions for this role
                db.query(RolePermission).filter(
                    RolePermission.role_id == db_role.id
                ).delete()
                
                # Create new permissions
                created_permissions = []
                for catalog_action_id in catalog_action_ids:
                    # Verify catalog_action exists
                    catalog_action = db.query(CatalogAction).filter(
                        CatalogAction.id == catalog_action_id
                    ).first()
                    
                    if not catalog_action:
                        continue  # Skip if catalog_action doesn't exist
                    
                    # Create the permission
                    db_permission = RolePermission(
                        role_id=db_role.id,
                        catalog_action_id=catalog_action_id,
                        is_allowed=True
                    )
                    db.add(db_permission)
                    created_permissions.append(catalog_action_id)
                
                if created_permissions:
                    db.commit()
                    permissions_updated = True
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="roles",
                description=f"Updated role: {db_role.role_code}" + (f" with {len(created_permissions)} permissions" if permissions_updated else ""),
                ip_address=ip_address,
                old_data=old_data,
                new_data={
                    "id": db_role.id,
                    "role_code": db_role.role_code,
                    "name": db_role.name,
                    "description": db_role.description,
                    "is_active": db_role.is_active,
                    "permissions_updated": permissions_updated
                },
                status="SUCCESS"
            )
            
            return db_role
        except IntegrityError:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="roles",
                description=f"Failed to update role ID: {role_id}",
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
        role_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Role]:
        """Delete a role."""
        db_role = self.get(db, role_id)
        
        if not db_role:
            return None
        
        # Store data before deletion
        old_data = {
            "id": db_role.id,
            "role_code": db_role.role_code,
            "name": db_role.name,
            "description": db_role.description,
            "is_active": db_role.is_active
        }
        
        db.delete(db_role)
        db.commit()
        
        # Log the delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="DELETE",
            module="roles",
            description=f"Deleted role: {old_data['role_code']} (ID: {role_id})",
            ip_address=ip_address,
            old_data=old_data,
            status="SUCCESS"
        )
        
        return db_role
    
    def soft_delete(
        self, 
        db: Session, 
        role_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Role]:
        """Soft delete a role by setting is_active to False."""
        db_role = self.get(db, role_id)
        
        if not db_role:
            return None
        
        old_status = db_role.is_active
        db_role.is_active = False
        db.commit()
        db.refresh(db_role)
        
        # Log the soft delete action
        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="SOFT_DELETE",
            module="roles",
            description=f"Soft deleted role: {db_role.role_code} (ID: {role_id})",
            ip_address=ip_address,
            old_data={"is_active": old_status},
            new_data={"is_active": False},
            status="SUCCESS"
        )
        
        return db_role


# Create a singleton instance
role = CRUDRole()
