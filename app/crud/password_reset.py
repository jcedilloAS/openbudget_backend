from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.password_reset import PasswordReset


class CRUDPasswordReset:

    def create(self, db: Session, *, user_id: int, token_hash: str, expires_at: datetime) -> PasswordReset:
        record = PasswordReset(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def get_by_token_hash(self, db: Session, token_hash: str) -> PasswordReset | None:
        return db.query(PasswordReset).filter(PasswordReset.token_hash == token_hash).first()

    def mark_as_used(self, db: Session, reset_record: PasswordReset) -> None:
        reset_record.used = True
        db.commit()

    def invalidate_user_tokens(self, db: Session, user_id: int) -> None:
        db.query(PasswordReset).filter(
            PasswordReset.user_id == user_id,
            PasswordReset.used == False,
        ).update({"used": True})
        db.commit()


password_reset = CRUDPasswordReset()
