#!/usr/bin/env python3
"""
Seed script for OpenBudget - Initial data setup
Run this script to populate the database with initial required data.

Usage:
    python seed_data.py
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.action import Action
from app.models.catalog import Catalog
from app.models.catalog_action import CatalogAction
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.system_configuration import SystemConfiguration


def seed_actions(db: Session):
    """Create basic actions (CRUD operations)."""
    print("🌱 Seeding Actions...")
    
    actions_data = [
        {"action_code": "list", "action_name": "List/View", "description": "View list of records"},
        {"action_code": "create", "action_name": "Create", "description": "Create new records"},
        {"action_code": "update", "action_name": "Update", "description": "Update existing records"},
        {"action_code": "delete", "action_name": "Delete", "description": "Delete records"},
        {"action_code": "export", "action_name": "Export", "description": "Export data"},
    ]
    
    created_count = 0
    for action_data in actions_data:
        existing = db.query(Action).filter(Action.action_code == action_data["action_code"]).first()
        if not existing:
            action = Action(**action_data)
            db.add(action)
            created_count += 1
    
    db.commit()
    print(f"   ✅ Created {created_count} actions")


def seed_catalogs(db: Session):
    """Create catalogs for all system resources."""
    print("🌱 Seeding Catalogs...")
    
    catalogs_data = [
        {"catalog_code": "users", "catalog_name": "Users", "description": "User management"},
        {"catalog_code": "roles", "catalog_name": "Roles", "description": "Role management"},
        {"catalog_code": "suppliers", "catalog_name": "Suppliers", "description": "Supplier management"},
        {"catalog_code": "projects", "catalog_name": "Projects", "description": "Project management"},
        {"catalog_code": "accounts", "catalog_name": "Accounts", "description": "Account management"},
        {"catalog_code": "retentions", "catalog_name": "Retentions", "description": "Retention management"},
        {"catalog_code": "catalogs", "catalog_name": "Catalogs", "description": "Catalog management"},
        {"catalog_code": "actions", "catalog_name": "Actions", "description": "Action management"},
        {"catalog_code": "permissions", "catalog_name": "Permissions", "description": "Permission management"},
        {"catalog_code": "system_configuration", "catalog_name": "System Configuration", "description": "System settings"},
        {"catalog_code": "audit_logs", "catalog_name": "Audit Logs", "description": "Audit log viewing"},
        {"catalog_code": "supplier_documents", "catalog_name": "Supplier Documents", "description": "Supplier document management"},
        {"catalog_code": "requisitions", "catalog_name": "Requisitions", "description": "Requisition management"},
    ]
    
    created_count = 0
    for catalog_data in catalogs_data:
        existing = db.query(Catalog).filter(Catalog.catalog_code == catalog_data["catalog_code"]).first()
        if not existing:
            catalog = Catalog(**catalog_data)
            db.add(catalog)
            created_count += 1
    
    db.commit()
    print(f"   ✅ Created {created_count} catalogs")


def seed_catalog_actions(db: Session):
    """Create catalog-action combinations (permissions)."""
    print("🌱 Seeding Catalog Actions...")
    
    # Define which actions apply to which catalogs
    catalog_action_map = {
        "users": ["list", "create", "update", "delete"],
        "roles": ["list", "create", "update", "delete"],
        "suppliers": ["list", "create", "update", "delete", "export"],
        "projects": ["list", "create", "update", "delete", "export"],
        "accounts": ["list", "create", "update", "delete", "export"],
        "retentions": ["list", "create", "update", "delete", "export"],
        "catalogs": ["list", "create", "update", "delete"],
        "actions": ["list", "create", "update", "delete"],
        "permissions": ["list", "create", "update", "delete"],
        "system_configuration": ["list", "create", "update"],
        "audit_logs": ["list", "export"],
        "supplier_documents": ["list", "create", "update", "delete"],
        "requisitions": ["list", "create", "update", "delete", "export"],
    }
    
    created_count = 0
    for catalog_code, action_codes in catalog_action_map.items():
        catalog = db.query(Catalog).filter(Catalog.catalog_code == catalog_code).first()
        if not catalog:
            continue
        
        for action_code in action_codes:
            action = db.query(Action).filter(Action.action_code == action_code).first()
            if not action:
                continue
            
            existing = db.query(CatalogAction).filter(
                CatalogAction.catalog_id == catalog.id,
                CatalogAction.action_id == action.id
            ).first()
            
            if not existing:
                catalog_action = CatalogAction(
                    catalog_id=catalog.id,
                    action_id=action.id,
                    is_active=True
                )
                db.add(catalog_action)
                created_count += 1
    
    db.commit()
    print(f"   ✅ Created {created_count} catalog-action combinations")


def seed_roles(db: Session):
    """Create default roles."""
    print("🌱 Seeding Roles...")
    
    roles_data = [
        {
            "role_code": "superadmin",
            "name": "Super Administrator",
            "description": "Full system access with all permissions"
        },
        {
            "role_code": "admin",
            "name": "Administrator",
            "description": "Administrative access to most features"
        },
        {
            "role_code": "manager",
            "name": "Manager",
            "description": "Manager with create/update permissions"
        },
        {
            "role_code": "user",
            "name": "User",
            "description": "Standard user with limited permissions"
        },
        {
            "role_code": "viewer",
            "name": "Viewer",
            "description": "Read-only access"
        },
    ]
    
    created_count = 0
    for role_data in roles_data:
        existing = db.query(Role).filter(Role.role_code == role_data["role_code"]).first()
        if not existing:
            role = Role(**role_data)
            db.add(role)
            created_count += 1
    
    db.commit()
    print(f"   ✅ Created {created_count} roles")


def seed_role_permissions(db: Session):
    """Assign permissions to roles."""
    print("🌱 Seeding Role Permissions...")
    
    # Define permission sets for each role
    role_permissions_map = {
        "superadmin": "all",  # Special case: all permissions
        "admin": {
            "users": ["list", "create", "update"],
            "roles": ["list"],
            "suppliers": ["list", "create", "update", "delete", "export"],
            "projects": ["list", "create", "update", "delete", "export"],
            "accounts": ["list", "create", "update", "delete", "export"],
            "retentions": ["list", "create", "update", "delete", "export"],
            "requisitions": ["list", "create", "update", "delete", "export"],
            "system_configuration": ["list", "create", "update"],
            "audit_logs": ["list", "export"],
            "supplier_documents": ["list", "create", "update", "delete"],
        },
        "manager": {
            "suppliers": ["list", "create", "update", "export"],
            "projects": ["list", "create", "update", "export"],
            "accounts": ["list", "create", "update", "export"],
            "retentions": ["list", "create", "update", "export"],
            "requisitions": ["list", "create", "update", "export"],
            "supplier_documents": ["list", "create", "update"],
        },
        "user": {
            "suppliers": ["list", "create", "update"],
            "projects": ["list"],
            "accounts": ["list", "create", "update"],
            "retentions": ["list", "create", "update"],
            "requisitions": ["list", "create"],
            "supplier_documents": ["list", "create"],
        },
        "viewer": {
            "suppliers": ["list"],
            "projects": ["list"],
            "accounts": ["list"],
            "retentions": ["list"],
            "requisitions": ["list"],
            "audit_logs": ["list"],
            "supplier_documents": ["list"],
        },
    }
    
    created_count = 0
    
    for role_code, permissions in role_permissions_map.items():
        role = db.query(Role).filter(Role.role_code == role_code).first()
        if not role:
            continue
        
        if permissions == "all":
            # Grant all permissions to superadmin
            all_catalog_actions = db.query(CatalogAction).all()
            for ca in all_catalog_actions:
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.catalog_action_id == ca.id
                ).first()
                
                if not existing:
                    role_permission = RolePermission(
                        role_id=role.id,
                        catalog_action_id=ca.id,
                        is_allowed=True
                    )
                    db.add(role_permission)
                    created_count += 1
        else:
            # Grant specific permissions
            for catalog_code, action_codes in permissions.items():
                catalog = db.query(Catalog).filter(Catalog.catalog_code == catalog_code).first()
                if not catalog:
                    continue
                
                for action_code in action_codes:
                    action = db.query(Action).filter(Action.action_code == action_code).first()
                    if not action:
                        continue
                    
                    catalog_action = db.query(CatalogAction).filter(
                        CatalogAction.catalog_id == catalog.id,
                        CatalogAction.action_id == action.id
                    ).first()
                    
                    if not catalog_action:
                        continue
                    
                    existing = db.query(RolePermission).filter(
                        RolePermission.role_id == role.id,
                        RolePermission.catalog_action_id == catalog_action.id
                    ).first()
                    
                    if not existing:
                        role_permission = RolePermission(
                            role_id=role.id,
                            catalog_action_id=catalog_action.id,
                            is_allowed=True
                        )
                        db.add(role_permission)
                        created_count += 1
    
    db.commit()
    print(f"   ✅ Created {created_count} role permissions")


def seed_users(db: Session):
    """Create initial superadmin user."""
    print("🌱 Seeding Users...")
    
    # Check if any user exists
    existing_user = db.query(User).first()
    if existing_user:
        print("   ⏭️  Users already exist, skipping...")
        return
    
    # Get superadmin role
    superadmin_role = db.query(Role).filter(Role.role_code == "superadmin").first()
    if not superadmin_role:
        print("   ⚠️  Superadmin role not found, skipping user creation")
        return
    
    # Create superadmin user
    admin_user = User(
        username="admin",
        name="System Administrator",
        email="admin@openbudget.com",
        password_hash=get_password_hash("admin123"),  # Change this in production!
        role_id=superadmin_role.id,
        is_active=True,
        is_superuser=True
    )
    
    db.add(admin_user)
    db.commit()
    print(f"   ✅ Created superadmin user")
    print(f"      Username: admin")
    print(f"      Password: admin123")
    print(f"      ⚠️  CHANGE PASSWORD IN PRODUCTION!")


def seed_system_configuration(db: Session):
    """Create initial system configuration."""
    print("🌱 Seeding System Configuration...")
    
    existing = db.query(SystemConfiguration).first()
    if existing:
        print("   ⏭️  System configuration already exists, skipping...")
        return
    
    # Get admin user for created_by
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    config = SystemConfiguration(
        company_name="OpenBudget Company",
        rfc="RFC000000000",
        smtp_host="smtp.gmail.com",
        smtp_port="587",
        smtp_encryption="TLS",
        created_by=admin_user.id if admin_user else None,
        updated_by=admin_user.id if admin_user else None,
    )
    
    db.add(config)
    db.commit()
    print(f"   ✅ Created system configuration")


def run_seed():
    """Run all seed functions."""
    print("\n" + "="*60)
    print("🚀 OpenBudget Database Seeding")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # Seed in order (respecting foreign key dependencies)
        seed_actions(db)
        seed_catalogs(db)
        seed_catalog_actions(db)
        seed_roles(db)
        seed_role_permissions(db)
        seed_users(db)
        seed_system_configuration(db)
        
        print("\n" + "="*60)
        print("✅ Database seeding completed successfully!")
        print("="*60 + "\n")
        print("📝 Next steps:")
        print("   1. Login with: admin / admin123")
        print("   2. Change the admin password immediately")
        print("   3. Create additional users as needed")
        print("   4. Configure system settings")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
