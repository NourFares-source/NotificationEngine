from datetime import datetime
import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text , UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    
    
    
class NotificationMetrics(Base):
    __tablename__ = "notification_metrics"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)  # e.g., 'completed', 'failed'
    timestamp = Column(DateTime, nullable=False, index=True) # Truncated to the hour
    count = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (
        UniqueConstraint("event_type", "timestamp", name="uq_event_timestamp"),
    )