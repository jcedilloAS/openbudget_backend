import asyncio
import logging
import threading
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.project import Project
from app.models.role_permission import RolePermission
from app.models.catalog_action import CatalogAction
from app.models.catalog import Catalog
from app.models.action import Action
from app.crud.notification import notification as crud_notification
from app.schemas.notification import NotificationCreate
from app.utils.notification_manager import notification_manager

logger = logging.getLogger(__name__)


def _get_approver_user_ids(db: Session) -> list[int]:
    """Return IDs of active users whose role has requisitions:approve permission or are superusers."""
    approver_role_ids = (
        db.query(RolePermission.role_id)
        .join(CatalogAction, RolePermission.catalog_action_id == CatalogAction.id)
        .join(Catalog, CatalogAction.catalog_id == Catalog.id)
        .join(Action, CatalogAction.action_id == Action.id)
        .filter(
            and_(
                Catalog.catalog_code == "requisitions",
                Action.action_code == "approve",
                RolePermission.is_allowed == True,
                CatalogAction.is_active == True,
            )
        )
        .distinct()
        .all()
    )

    role_id_list = [r.role_id for r in approver_role_ids] if approver_role_ids else []

    # Get users with approve permission OR superusers
    users = (
        db.query(User.id)
        .filter(
            User.is_active == True,
            or_(
                User.role_id.in_(role_id_list) if role_id_list else False,
                User.is_superuser == True
            )
        )
        .all()
    )

    return [u.id for u in users]


def notify_approvers_sync(
    db: Session,
    requisition_id: int,
    requisition_number: str,
    project_id: int,
    submitted_by_id: int,
) -> None:
    """Synchronous version: Persist notifications and push SSE events to all users with approve permission."""
    
    # Get data for notification message
    submitter = db.query(User).filter(User.id == submitted_by_id).first()
    project = db.query(Project).filter(Project.id == project_id).first()
    
    submitter_name = submitter.name if submitter else f"User {submitted_by_id}"
    project_name = project.name if project else f"Project {project_id}"
    
    user_ids = _get_approver_user_ids(db)

    if not user_ids:
        logger.warning("notify_approvers_sync: no approver users found for requisitions:approve")
        return

    title = "Nueva requisición pendiente de aprobación"
    message = f"{submitter_name} envió la requisición {requisition_number} del proyecto {project_name}."
    data = {
        "requisition_id": requisition_id,
        "requisition_number": requisition_number,
        "project_name": project_name,
        "submitted_by": submitter_name,
    }

    # Persist one notification per approver (synchronous)
    for user_id in user_ids:
        try:
            crud_notification.create(
                db,
                NotificationCreate(
                    user_id=user_id,
                    type="requisition_submitted",
                    title=title,
                    message=message,
                    data=data,
                ),
            )
            logger.info(f"Created notification for user {user_id} - requisition {requisition_number}")
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}")

    # Push SSE to connected approvers (async in background thread)
    sse_payload = {
        "type": "requisition_submitted",
        "title": title,
        "message": message,
        "data": data,
    }
    
    def _broadcast_sse():
        """Run async broadcast in a new event loop."""
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(notification_manager.broadcast(user_ids, sse_payload))
            new_loop.close()
            logger.info(f"SSE broadcast sent to {len(user_ids)} approvers")
        except Exception as e:
            logger.error(f"Error broadcasting SSE: {e}")
    
    # Run in background thread to not block the response
    thread = threading.Thread(target=_broadcast_sse, daemon=True)
    thread.start()


async def notify_approvers(
    db: Session,
    requisition_id: int,
    requisition_number: str,
    project_name: str,
    submitted_by_name: str,
) -> None:
    """Persist notifications and push SSE events to all users with approve permission."""
    user_ids = _get_approver_user_ids(db)

    if not user_ids:
        logger.warning("notify_approvers: no approver users found for requisitions:approve")
        return

    title = "Nueva requisición pendiente de aprobación"
    message = f"{submitted_by_name} envió la requisición {requisition_number} del proyecto {project_name}."
    data = {
        "requisition_id": requisition_id,
        "requisition_number": requisition_number,
        "project_name": project_name,
        "submitted_by": submitted_by_name,
    }

    # Persist one notification per approver
    for user_id in user_ids:
        crud_notification.create(
            db,
            NotificationCreate(
                user_id=user_id,
                type="requisition_submitted",
                title=title,
                message=message,
                data=data,
            ),
        )

    # Push SSE to connected approvers
    sse_payload = {
        "type": "requisition_submitted",
        "title": title,
        "message": message,
        "data": data,
    }
    await notification_manager.broadcast(user_ids, sse_payload)


def notify_requester_sync(
    db: Session,
    requisition_id: int,
    requisition_number: str,
    project_id: int,
    requester_user_id: int,
    action: str,
    acted_by_id: int,
    rejection_reason: str | None = None,
) -> None:
    """Notify the requester that their requisition was approved or rejected."""

    actor = db.query(User).filter(User.id == acted_by_id).first()
    project = db.query(Project).filter(Project.id == project_id).first()

    actor_name = actor.name if actor else f"User {acted_by_id}"
    project_name = project.name if project else f"Project {project_id}"

    if action == "approved":
        notif_type = "requisition_approved"
        title = "Requisición aprobada"
        message = f"{actor_name} aprobó tu requisición {requisition_number} del proyecto {project_name}."
    else:
        notif_type = "requisition_rejected"
        title = "Requisición rechazada"
        message = f"{actor_name} rechazó tu requisición {requisition_number} del proyecto {project_name}."
        if rejection_reason:
            message += f" Motivo: {rejection_reason}"

    data = {
        "requisition_id": requisition_id,
        "requisition_number": requisition_number,
        "project_name": project_name,
        "action": action,
        "acted_by": actor_name,
    }
    if rejection_reason:
        data["rejection_reason"] = rejection_reason

    try:
        crud_notification.create(
            db,
            NotificationCreate(
                user_id=requester_user_id,
                type=notif_type,
                title=title,
                message=message,
                data=data,
            ),
        )
        logger.info(f"Created {action} notification for user {requester_user_id} - requisition {requisition_number}")
    except Exception as e:
        logger.error(f"Error creating {action} notification for user {requester_user_id}: {e}")

    # Push SSE in background thread
    sse_payload = {"type": notif_type, "title": title, "message": message, "data": data}

    def _send_sse():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(notification_manager.send(requester_user_id, sse_payload))
            loop.close()
        except Exception as e:
            logger.error(f"Error sending SSE to user {requester_user_id}: {e}")

    thread = threading.Thread(target=_send_sse, daemon=True)
    thread.start()
