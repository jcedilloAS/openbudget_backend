from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.crud.action import action
from app.schemas.action import Action, ActionCreate, ActionUpdate, ActionList
from app.utils.request import get_client_ip

router = APIRouter()


@router.get("/", response_model=ActionList, summary="List all actions")
def list_actions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("actions", "list"))
):
    """
    Retrieve a list of actions with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    actions = action.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    total = action.count(db, is_active=is_active)
    
    return ActionList(total=total, items=actions)


@router.get("/{action_id}", response_model=Action, summary="Get action by ID")
def get_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("actions", "list"))
):
    """
    Retrieve a specific action by ID.
    
    - **action_id**: The ID of the action to retrieve
    """
    db_action = action.get(db, action_id=action_id)
    
    if not db_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found"
        )
    
    return db_action


@router.post("/", response_model=Action, status_code=status.HTTP_201_CREATED, summary="Create new action")
def create_action(
    action_in: ActionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("actions", "create"))
):
    """
    Create a new action.
    
    - **action_code**: Unique action code (required)
    - **action_name**: Action name (required)
    - **description**: Optional description of the action
    - **is_active**: Whether the action is active (default: true)
    """
    ip_address = get_client_ip(request)
    return action.create(
        db, 
        action_in=action_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )


@router.put("/{action_id}", response_model=Action, summary="Update action")
def update_action(
    action_id: int,
    action_in: ActionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("actions", "update"))
):
    """
    Update an existing action.
    
    - **action_id**: The ID of the action to update
    - **action_code**: New action code (optional)
    - **action_name**: New name (optional)
    - **description**: New description (optional)
    - **is_active**: New active status (optional)
    """
    ip_address = get_client_ip(request)
    db_action = action.update(
        db, 
        action_id=action_id, 
        action_in=action_in,
        current_user_id=current_user.id,
        ip_address=ip_address
    )
    
    if not db_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found"
        )
    
    return db_action


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete action")
def delete_action(
    action_id: int,
    soft: bool = Query(False, description="Perform soft delete (set is_active=False)"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("actions", "delete"))
):
    """
    Delete an action.
    
    - **action_id**: The ID of the action to delete
    - **soft**: If true, performs soft delete (sets is_active=False). If false, permanently deletes the record.
    """
    ip_address = get_client_ip(request) if request else "unknown"
    
    if soft:
        db_action = action.soft_delete(
            db, 
            action_id=action_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    else:
        db_action = action.delete(
            db, 
            action_id=action_id,
            current_user_id=current_user.id,
            ip_address=ip_address
        )
    
    if not db_action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found"
        )
    
    return None


@router.get("/search/", response_model=ActionList, summary="Search actions")
def search_actions(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("actions", "list"))
):
    """
    Search actions by action_code or action_name.
    
    - **q**: Search term (required)
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Optional filter by active status
    """
    actions = action.search(db, search_term=q, skip=skip, limit=limit, is_active=is_active)
    total = len(actions)
    
    return ActionList(total=total, items=actions)
