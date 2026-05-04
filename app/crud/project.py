from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.project import Project
from app.models.user import User
from app.models.user_project import UserProject
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectSummary, ProjectBulkUploadResult, ProjectBulkUploadError
from app.utils.audit import AuditLogger


class CRUDProject:
    """CRUD operations for Project model."""
    
    def get(self, db: Session, project_id: int) -> Optional[Project]:
        """Get a single project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()
    
    def get_with_members(self, db: Session, project_id: int) -> Optional[Project]:
        """Get a single project by ID with project members eager loaded."""
        return db.query(Project).options(
            joinedload(Project.project_members)
        ).filter(Project.id == project_id).first()
    
    def get_by_project_code(self, db: Session, project_code: str) -> Optional[Project]:
        """Get a single project by project code."""
        return db.query(Project).filter(Project.project_code == project_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> List[Project]:
        """Get multiple projects with pagination and optional filtering."""
        query = db.query(Project)
        
        if status is not None:
            query = query.filter(Project.status == status)
        
        if created_by is not None:
            query = query.filter(Project.created_by == created_by)
        
        return query.order_by(Project.id).offset(skip).limit(limit).all()
    
    def count(
        self, 
        db: Session, 
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """Count total projects with optional filtering."""
        query = db.query(Project)
        
        if status is not None:
            query = query.filter(Project.status == status)
        
        if created_by is not None:
            query = query.filter(Project.created_by == created_by)
        
        return query.count()
    
    def create(
        self, 
        db: Session, 
        project_in: ProjectCreate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        # Check if project code already exists
        existing_project = self.get_by_project_code(db, project_in.project_code)
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with code '{project_in.project_code}' already exists"
            )
        
        # Validate user_ids exist before creating the project
        user_ids_list = []
        if project_in.user_ids:
            existing_users = db.query(User.id).filter(User.id.in_(project_in.user_ids)).all()
            existing_ids = {u.id for u in existing_users}
            invalid_ids = [uid for uid in project_in.user_ids if uid not in existing_ids]
            if invalid_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The following user IDs do not exist: {invalid_ids}"
                )
            user_ids_list = list(project_in.user_ids)
        
        db_project = Project(
            project_code=project_in.project_code,
            name=project_in.name,
            description=project_in.description,
            initial_budget=project_in.initial_budget,
            commited=project_in.commited,
            spent=project_in.spent,
            available_balance=project_in.initial_budget,  # Set available_balance equal to initial_budget
            status=project_in.status,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        try:
            db.add(db_project)
            db.flush()  # Flush to get project ID without committing
            
            # Create user-project associations if user_ids provided
            if user_ids_list:
                for user_id in user_ids_list:
                    user_project = UserProject(
                        user_id=user_id,
                        project_id=db_project.id
                    )
                    db.add(user_project)
            
            db.commit()
            db.refresh(db_project)
            
            # Log the create action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="projects",
                description=f"Created project: {db_project.project_code}",
                ip_address=ip_address,
                new_data={
                    "id": db_project.id,
                    "project_code": db_project.project_code,
                    "name": db_project.name,
                    "initial_budget": float(db_project.initial_budget),
                    "status": db_project.status,
                    "user_ids": user_ids_list
                },
                status="SUCCESS"
            )
            
            return db_project
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="CREATE",
                module="projects",
                description=f"Failed to create project: {project_in.project_code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if user IDs exist."
            )
    
    def update(
        self, 
        db: Session, 
        project_id: int, 
        project_in: ProjectUpdate,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Project]:
        """Update an existing project."""
        db_project = self.get(db, project_id)
        
        if not db_project:
            return None
        
        # Store old data for audit
        old_data = {
            "id": db_project.id,
            "project_code": db_project.project_code,
            "name": db_project.name,
            "initial_budget": float(db_project.initial_budget),
            "commited": float(db_project.commited),
            "spent": float(db_project.spent),
            "status": db_project.status
        }
        
        # Check if new project code already exists (if being updated)
        if project_in.project_code and project_in.project_code != db_project.project_code:
            existing_project = self.get_by_project_code(db, project_in.project_code)
            if existing_project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project with code '{project_in.project_code}' already exists"
                )
        
        # Update only provided fields
        update_data = project_in.model_dump(exclude_unset=True)
        
        # Handle user_ids separately
        user_ids = update_data.pop("user_ids", None)
        
        # Validate user_ids exist
        if user_ids is not None and user_ids:
            existing_users = db.query(User.id).filter(User.id.in_(user_ids)).all()
            existing_ids = {u.id for u in existing_users}
            invalid_ids = [uid for uid in user_ids if uid not in existing_ids]
            if invalid_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The following user IDs do not exist: {invalid_ids}"
                )
        
        for field, value in update_data.items():
            setattr(db_project, field, value)
        
        # Update the updated_by field
        db_project.updated_by = current_user_id
        
        try:
            # Update user-project associations if user_ids provided
            if user_ids is not None:
                # Delete existing associations
                db.query(UserProject).filter(UserProject.project_id == project_id).delete()
                
                # Create new associations
                for user_id in user_ids:
                    user_project = UserProject(
                        user_id=user_id,
                        project_id=project_id
                    )
                    db.add(user_project)
            
            db.commit()
            db.refresh(db_project)
            
            # Store new data for audit
            new_data = {
                "id": db_project.id,
                "project_code": db_project.project_code,
                "name": db_project.name,
                "initial_budget": float(db_project.initial_budget),
                "commited": float(db_project.commited),
                "spent": float(db_project.spent),
                "status": db_project.status
            }
            
            # Log the update action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="projects",
                description=f"Updated project: {db_project.project_code}",
                ip_address=ip_address,
                old_data=old_data,
                new_data=new_data,
                status="SUCCESS"
            )
            
            return db_project
        except IntegrityError as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="UPDATE",
                module="projects",
                description=f"Failed to update project: {db_project.project_code}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error occurred. Check if user IDs exist."
            )
    
    def delete(
        self, 
        db: Session, 
        project_id: int,
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> Optional[Project]:
        """Delete a project."""
        db_project = self.get(db, project_id)
        
        if not db_project:
            return None
        
        # Store data for audit before deletion
        project_data = {
            "id": db_project.id,
            "project_code": db_project.project_code,
            "name": db_project.name,
            "initial_budget": float(db_project.initial_budget),
            "status": db_project.status
        }
        
        try:
            db.delete(db_project)
            db.commit()
            
            # Log the delete action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="projects",
                description=f"Deleted project: {project_data['project_code']}",
                ip_address=ip_address,
                old_data=project_data,
                status="SUCCESS"
            )
            
            return db_project
        except Exception as e:
            db.rollback()
            
            # Log the failed action
            AuditLogger.log_action(
                db=db,
                user_id=current_user_id,
                action="DELETE",
                module="projects",
                description=f"Failed to delete project: {project_data['project_code']}",
                ip_address=ip_address,
                status="FAILURE",
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting project: {str(e)}"
            )
    
    def update_budget(
        self, 
        db: Session, 
        project_id: int,
        commited: Optional[Decimal] = None,
        spent: Optional[Decimal] = None,
        updated_by: int = None,
        ip_address: Optional[str] = None
    ) -> Optional[Project]:
        """Update project budget fields and recalculate available balance."""
        db_project = self.get(db, project_id)
        
        if not db_project:
            return None
        
        # Store old data for audit
        old_data = {
            "commited": float(db_project.commited),
            "spent": float(db_project.spent),
            "available_balance": float(db_project.available_balance)
        }
        
        if commited is not None:
            db_project.commited = commited
        
        if spent is not None:
            db_project.spent = spent
        
        # Recalculate available balance
        db_project.available_balance = db_project.initial_budget - db_project.commited - db_project.spent
        
        if updated_by is not None:
            db_project.updated_by = updated_by
        
        db.commit()
        db.refresh(db_project)
        
        # Store new data for audit
        new_data = {
            "commited": float(db_project.commited),
            "spent": float(db_project.spent),
            "available_balance": float(db_project.available_balance)
        }
        
        # Log the budget update action
        if updated_by:
            AuditLogger.log_action(
                db=db,
                user_id=updated_by,
                action="UPDATE_BUDGET",
                module="projects",
                description=f"Updated budget for project: {db_project.project_code}",
                ip_address=ip_address,
                old_data=old_data,
                new_data=new_data,
                status="SUCCESS"
            )
        
        return db_project
    
    def get_summary(self, db: Session, status: Optional[str] = None) -> ProjectSummary:
        """Get budget summary for all projects or filtered by status."""
        query = db.query(
            func.count(Project.id).label("total_projects"),
            func.coalesce(func.sum(Project.initial_budget), 0).label("total_initial_budget"),
            func.coalesce(func.sum(Project.commited), 0).label("total_commited"),
            func.coalesce(func.sum(Project.spent), 0).label("total_spent"),
            func.coalesce(func.sum(Project.available_balance), 0).label("total_available")
        )
        
        if status is not None:
            query = query.filter(Project.status == status)
        
        result = query.first()
        
        return ProjectSummary(
            total_projects=result.total_projects,
            total_initial_budget=Decimal(str(result.total_initial_budget)),
            total_commited=Decimal(str(result.total_commited)),
            total_spent=Decimal(str(result.total_spent)),
            total_available=Decimal(str(result.total_available))
        )
    
    def get_by_status(self, db: Session, status: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects by status."""
        return db.query(Project)\
            .filter(Project.status == status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def search(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Search projects by project_code, name, or description."""
        pattern = f"%{search_term}%"
        return (
            db.query(Project)
            .filter(
                (Project.project_code.ilike(pattern)) |
                (Project.name.ilike(pattern)) |
                (Project.description.ilike(pattern))
            )
            .order_by(Project.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def bulk_create(
        self,
        db: Session,
        rows: List[tuple],
        current_user_id: int,
        ip_address: Optional[str] = None
    ) -> ProjectBulkUploadResult:
        """Bulk create projects from a list of rows. Col 0 = project_code, Col 1 = name."""
        created, failed = 0, 0
        errors: List[ProjectBulkUploadError] = []

        for row_idx, row in enumerate(rows, start=2):  # start=2: row 1 is header
            project_code = str(row[0] or "").strip() if len(row) > 0 else ""
            name = str(row[1] or "").strip() if len(row) > 1 else ""
            print(f'project_code: {project_code} name: {name} ')
            if not project_code or not name:
                failed += 1
                errors.append(ProjectBulkUploadError(
                    row=row_idx,
                    project_code=project_code or None,
                    error="project_code and name are required"
                ))
                continue

            try:
                project_in = ProjectCreate(project_code=project_code, name=name)
                self.create(db, project_in=project_in, current_user_id=current_user_id, ip_address=ip_address)
                created += 1
            except HTTPException as e:
                failed += 1
                errors.append(ProjectBulkUploadError(
                    row=row_idx,
                    project_code=project_code,
                    error=e.detail
                ))
            except Exception as e:
                failed += 1
                errors.append(ProjectBulkUploadError(
                    row=row_idx,
                    project_code=project_code,
                    error=str(e)
                ))

        AuditLogger.log_action(
            db=db,
            user_id=current_user_id,
            action="BULK_CREATE",
            module="projects",
            description=f"Bulk upload: {created} created, {failed} failed",
            ip_address=ip_address,
            new_data={"created": created, "failed": failed},
            status="SUCCESS" if failed == 0 else "PARTIAL"
        )

        return ProjectBulkUploadResult(
            total_rows=created + failed,
            created=created,
            failed=failed,
            errors=errors
        )


# Create a singleton instance
project = CRUDProject()
