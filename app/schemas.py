from pydantic import BaseModel
from datetime import datetime
from app.models import NotificationStatus

class NotificationCreate(BaseModel):
    recipient: str
    message: str

class NotificationResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: NotificationStatus
    created_at: datetime

    class Config:
        from_attributes = True