from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.project import project
from app.schemas.project import (
    Project, 
    ProjectCreate, 
    ProjectUpdate, 
    ProjectList, 
    ProjectWithUsers,
    ProjectWithMembers,
    ProjectSummary
)
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=ProjectList, summary="List all projects")
def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list"))
):
    """
    Retrieve a list of projects with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **status**: Optional filter by status (ACTIVE, COMPLETED, CANCELLED, etc.)
    - **created_by**: Optional filter by creator user ID
    """
    projects = project.get_multi(db, skip=skip, limit=limit, status=status, created_by=created_by)
    total = project.count(db, status=status, created_by=created_by)
    
    return ProjectList(total=total, items=projects)


@router.get("/summary", response_model=ProjectSummary, summary="Get projects budget summary")
def get_projects_summary(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list"))
):
    """
    Get budget summary for all projects or filtered by status.
    
    - **status**: Optional filter by status
    
    Returns totals for: projects count, initial budget, committed, spent, and available balance.
    """
    return project.get_summary(db, status=status)


@router.get("/{project_id}", response_model=ProjectWithUsers, summary="Get project by ID")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list"))
):
    """
    Retrieve a specific project by ID.
    
    - **project_id**: The ID of the project to retrieve
    """
    db_project = project.get(db, project_id=project_id)
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return db_project


@router.get("/{project_id}/members", response_model=ProjectWithMembers, summary="Get project with team members")
def get_project_with_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list"))
):
    """
    Retrieve a specific project by ID with all assigned team members.
    
    - **project_id**: The ID of the project to retrieve
    """
    db_project = project.get_with_members(db, project_id=project_id)
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return db_project


@router.get("/code/{project_code}", response_model=Project, summary="Get project by code")
def get_project_by_code(
    project_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list"))
):
    """
    Retrieve a specific project by project code.
    
    - **project_code**: The unique code of the project to retrieve
    """
    db_project = project.get_by_project_code(db, project_code=project_code)
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with code '{project_code}' not found"
        )
    
    return db_project


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED, summary="Create new project")
def create_project(
    project_in: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "create"))
):
    """
    Create a new project.
    
    - **project_code**: Unique project code (required)
    - **name**: Project name (required)
    - **description**: Optional description
    - **initial_budget**: Initial budget amount
    - **commited**: Committed amount
    - **spent**: Spent amount
    - **available_balance**: Available balance
    - **status**: Project status (default: ACTIVE)
    - **created_by**: User ID who created the project (required)
    - **updated_by**: User ID who last updated the project (required)
    """
    ip_address = get_client_ip(request)
    return project.create(
        db, 
        project_in=project_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{project_id}", response_model=Project, summary="Update project")
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "update"))
):
    """
    Update an existing project.
    
    - **project_id**: The ID of the project to update
    - **project_code**: New project code (optional)
    - **name**: New name (optional)
    - **description**: New description (optional)
    - **initial_budget**: New initial budget (optional)
    - **commited**: New committed amount (optional)
    - **spent**: New spent amount (optional)
    - **available_balance**: New available balance (optional)
    - **status**: New status (optional)
    - **user_ids**: New list of user IDs to assign to the project (optional)
    
    The project will be updated by the authenticated user automatically.
    """
    ip_address = get_client_ip(request)
    db_project = project.update(
        db, 
        project_id=project_id, 
        project_in=project_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return db_project


@router.patch("/{project_id}/budget", response_model=Project, summary="Update project budget")
def update_project_budget(
    project_id: int,
    request: Request,
    commited: Optional[Decimal] = Query(None, description="New committed amount"),
    spent: Optional[Decimal] = Query(None, description="New spent amount"),
    updated_by: int = Query(..., description="User ID updating the budget"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "update"))
):
    """
    Update project budget fields and automatically recalculate available balance.
    
    - **project_id**: The ID of the project to update
    - **commited**: New committed amount (optional)
    - **spent**: New spent amount (optional)
    - **updated_by**: User ID who is updating the budget (required)
    
    Available balance is automatically calculated as: initial_budget - commited - spent
    """
    ip_address = get_client_ip(request)
    db_project = project.update_budget(
        db, 
        project_id=project_id, 
        commited=commited, 
        spent=spent,
        updated_by=updated_by,
        ip_address=ip_address
    )
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
def delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "delete"))
):
    """
    Delete a project.
    
    - **project_id**: The ID of the project to delete
    """
    ip_address = get_client_ip(request)
    db_project = project.delete(
        db, 
        project_id=project_id,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return None


@router.get("/status/{status}", response_model=ProjectList, summary="Get projects by status")
def get_projects_by_status(
    status: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("projects", "list"))
):
    """
    Retrieve projects filtered by status.
    
    - **status**: The status to filter by (ACTIVE, COMPLETED, CANCELLED, etc.)
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    projects = project.get_by_status(db, status=status, skip=skip, limit=limit)
    total = project.count(db, status=status)
    
    return ProjectList(total=total, items=projects)
