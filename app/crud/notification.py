from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate


class CRUDNotification:
    """CRUD operations for Notification model."""

    def create(self, db: Session, notification_in: NotificationCreate) -> Notification:
        db_notification = Notification(**notification_in.model_dump())
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification

    def get_multi(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        is_read: Optional[bool] = None,
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def count(self, db: Session, user_id: int, is_read: Optional[bool] = None) -> int:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        return query.count()

    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        db_notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not db_notification:
            return None
        db_notification.is_read = True
        db.commit()
        db.refresh(db_notification)
        return db_notification

    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        updated = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True})
        )
        db.commit()
        return updated


notification = CRUDNotification()
