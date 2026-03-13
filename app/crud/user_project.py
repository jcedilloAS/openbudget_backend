from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.user_project import UserProject
from app.schemas.user_project import UserProjectCreate
from app.utils.audit import AuditLogger


class CRUDUserProject:
    """CRUD operations for UserProject model."""
    
    def get(self, db: Session, user_project_id: int) -> Optional[UserProject]:
        """Get a single user-project association by ID."""
        return db.query(UserProject).filter(UserProject.id == user_project_id).first()
    
    def get_by_user_and_project(
        self, 
        db: Session, 
        user_id: int, 
        project_id: int
    ) -> Optional[UserProject]:
        """Get a user-project association by user_id and project_id."""
        return db.query(UserProject).filter(
            UserProject.user_id == user_id,
            UserProject.project_id == project_id
        ).first()
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserProject]:
        """Get all projects for a specific user."""
        return db.query(UserProject)\
            .filter(UserProject.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_project(
        self, 
        db: Session, 
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserProject]:
        """Get all users for a specific project."""
        return db.query(UserProject)\
            .filter(UserProject.project_id == project_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserProject]:
        """Get multiple user-project associations with pagination."""
        return db.query(UserProject).offset(skip).limit(limit).all()
    
    def count(self, db: Session) -> int:
        """Count total user-project associations."""
        return db.query(UserProject).count()
    
    def count_by_user(self, db: Session, user_id: int) -> int:
        """Count total projects for a specific user."""
        return db.query(UserProject).filter(UserProject.user_id == user_id).count()
    
    def count_by_project(self, db: Session, project_id: int) -> int:
        """Count total users for a specific project."""
        return db.query(UserProject).filter(UserProject.project_id == project_id).count()
    
    def create(
        self, 
        db: Session, 
        user_project_in: UserProjectCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> UserProject:
        """Create a new user-project association."""
        # Check if association already exists
        existing = self.get_by_user_and_project(
            db, 
            user_project_in.user_id, 
            user_project_in.project_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_project_in.user_id} is already associated with project {user_project_in.project_id}"
            )
        
        db_user_project = UserProject(
            user_id=user_project_in.user_id,
            project_id=user_project_in.project_id
        )
        
        try:
            db.add(db_user_project)
            db.commit()
            db.refresh(db_user_project)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="user_projects",
                description=f"Assigned user {user_project_in.user_id} to project {user_project_in.project_id}",
                ip_address=ip_address,
                new_data={
                    "id": db_user_project.id,
                    "user_id": db_user_project.user_id,
                    "project_id": db_user_project.project_id
                },
                status="SUCCESS"
            )
            
            return db_user_project
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="user_projects",
                description=f"Failed to assign user {user_project_in.user_id} to project {user_project_in.project_id}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if user and project IDs exist."
            )
    
    def delete(
        self, 
        db: Session, 
        user_project_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[UserProject]:
        """Delete a user-project association."""
        db_user_project = self.get(db, user_project_id)
        
        if not db_user_project:
            return None
        
        # Store data for audit before deletion
        association_data = {
            "id": db_user_project.id,
            "user_id": db_user_project.user_id,
            "project_id": db_user_project.project_id
        }
        
        try:
            db.delete(db_user_project)
            db.commit()
            
            # Log the delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="user_projects",
                description=f"Removed user {association_data['user_id']} from project {association_data['project_id']}",
                ip_address=ip_address,
                old_data=association_data,
                status="SUCCESS"
            )
            
            return db_user_project
        except Exception as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="user_projects",
                description=f"Failed to remove user {association_data['user_id']} from project {association_data['project_id']}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting user-project association: {str(e)}"
            )
    
    def delete_by_user_and_project(
        self, 
        db: Session, 
        user_id: int, 
        project_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[UserProject]:
        """Delete a user-project association by user_id and project_id."""
        db_user_project = self.get_by_user_and_project(db, user_id, project_id)
        
        if not db_user_project:
            return None
        
        try:
            db.delete(db_user_project)
            db.commit()
            
            # Log the delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="user_projects",
                description=f"Removed user {user_id} from project {project_id}",
                ip_address=ip_address,
                old_data={"user_id": user_id, "project_id": project_id},
                status="SUCCESS"
            )
            
            return db_user_project
        except Exception as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="user_projects",
                description=f"Failed to remove user {user_id} from project {project_id}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting user-project association: {str(e)}"
            )
    
    def delete_all_by_user(
        self, 
        db: Session, 
        user_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> int:
        """Delete all project associations for a user. Returns count of deleted records."""
        count = db.query(UserProject).filter(UserProject.user_id == user_id).count()
        
        if count > 0:
            db.query(UserProject).filter(UserProject.user_id == user_id).delete()
            db.commit()
            
            # Log the bulk delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="BULK_DELETE",
                module="user_projects",
                description=f"Removed all project associations for user {user_id} (count: {count})",
                ip_address=ip_address,
                old_data={"user_id": user_id, "count": count},
                status="SUCCESS"
            )
        
        return count
    
    def delete_all_by_project(
        self, 
        db: Session, 
        project_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> int:
        """Delete all user associations for a project. Returns count of deleted records."""
        count = db.query(UserProject).filter(UserProject.project_id == project_id).count()
        
        if count > 0:
            db.query(UserProject).filter(UserProject.project_id == project_id).delete()
            db.commit()
            
            # Log the bulk delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="BULK_DELETE",
                module="user_projects",
                description=f"Removed all user associations for project {project_id} (count: {count})",
                ip_address=ip_address,
                old_data={"project_id": project_id, "count": count},
                status="SUCCESS"
            )
        
        return count


crud_user_project = CRUDUserProject()
