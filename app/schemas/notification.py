from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any, List


class NotificationBase(BaseModel):
    type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=500)
    data: Optional[Any] = None


class NotificationCreate(NotificationBase):
    user_id: int


class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationList(BaseModel):
    total: int
    items: List[Notification]

    model_config = ConfigDict(from_attributes=True)
