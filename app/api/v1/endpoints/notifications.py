import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.crud.notification import notification as crud_notification
from app.schemas.notification import Notification, NotificationList
from app.utils.notification_manager import notification_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stream", summary="SSE stream of real-time notifications")
async def notification_stream(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Open a Server-Sent Events stream for the authenticated user.
    The client will receive events in real time whenever a notification is dispatched.
    """
    queue = notification_manager.connect(current_user.id)

    async def event_generator():
        try:
            # Send a keep-alive comment every 30 seconds and yield queued events
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": data.get("type", "notification"),
                        "data": json.dumps(data),
                    }
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield {"event": "ping", "data": ""}
        except asyncio.CancelledError:
            pass
        finally:
            notification_manager.disconnect(current_user.id)

    return EventSourceResponse(event_generator())


@router.get("/", response_model=NotificationList, summary="List notifications for current user")
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve paginated notifications for the authenticated user.
    """
    items = crud_notification.get_multi(
        db, user_id=current_user.id, skip=skip, limit=limit, is_read=is_read
    )
    total = crud_notification.count(db, user_id=current_user.id, is_read=is_read)
    return NotificationList(total=total, items=items)


@router.patch("/{notification_id}/read", response_model=Notification, summary="Mark notification as read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a single notification as read."""
    db_notification = crud_notification.mark_as_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )
    return db_notification


@router.patch("/read-all", summary="Mark all notifications as read")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark all unread notifications for the current user as read."""
    updated = crud_notification.mark_all_as_read(db, user_id=current_user.id)
    return {"updated": updated}
