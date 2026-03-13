from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.crud.user_project import crud_user_project
from app.schemas.user_project import (
    UserProject,
    UserProjectCreate,
    UserProjectList
)
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=UserProjectList)
def get_user_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all user-project associations with pagination.
    """
    user_projects = crud_user_project.get_multi(db, skip=skip, limit=limit)
    total = crud_user_project.count(db)
    return UserProjectList(total=total, items=user_projects)


@router.get("/{user_project_id}", response_model=UserProject)
def get_user_project(
    user_project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific user-project association by ID.
    """
    user_project = crud_user_project.get(db, user_project_id=user_project_id)
    if not user_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserProject with id {user_project_id} not found"
        )
    return user_project


@router.get("/user/{user_id}", response_model=UserProjectList)
def get_projects_by_user(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all projects associated with a specific user.
    """
    user_projects = crud_user_project.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    total = crud_user_project.count_by_user(db, user_id=user_id)
    return UserProjectList(total=total, items=user_projects)


@router.get("/project/{project_id}", response_model=UserProjectList)
def get_users_by_project(
    project_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all users associated with a specific project.
    """
    user_projects = crud_user_project.get_by_project(db, project_id=project_id, skip=skip, limit=limit)
    total = crud_user_project.count_by_project(db, project_id=project_id)
    return UserProjectList(total=total, items=user_projects)


@router.post("/", response_model=UserProject, status_code=status.HTTP_201_CREATED)
def create_user_project(
    user_project_in: UserProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new user-project association.
    """
    ip_address = get_client_ip(request)
    return crud_user_project.create(
        db, 
        user_project_in=user_project_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.delete("/{user_project_id}", response_model=UserProject)
def delete_user_project(
    user_project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a user-project association by ID.
    """
    ip_address = get_client_ip(request)
    user_project = crud_user_project.delete(
        db, 
        user_project_id=user_project_id,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    if not user_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserProject with id {user_project_id} not found"
        )
    return user_project


@router.delete("/user/{user_id}/project/{project_id}", response_model=UserProject)
def delete_user_project_association(
    user_id: int,
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a user-project association by user_id and project_id.
    """
    ip_address = get_client_ip(request)
    user_project = crud_user_project.delete_by_user_and_project(
        db, 
        user_id=user_id, 
        project_id=project_id,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    if not user_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association between user {user_id} and project {project_id} not found"
        )
    return user_project


@router.delete("/user/{user_id}/all")
def delete_all_user_projects(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete all project associations for a user.
    """
    ip_address = get_client_ip(request)
    count = crud_user_project.delete_all_by_user(
        db, 
        user_id=user_id,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    return {"message": f"Deleted {count} project associations for user {user_id}"}


@router.delete("/project/{project_id}/all")
def delete_all_project_users(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete all user associations for a project.
    """
    ip_address = get_client_ip(request)
    count = crud_user_project.delete_all_by_project(
        db, 
        project_id=project_id,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    return {"message": f"Deleted {count} user associations for project {project_id}"}
