import logging
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from arq.connections import RedisSettings

from app.config import settings
from app.models import Notification, NotificationStatus, NotificationMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup(ctx: dict):
    logger.info("Worker process starting up... Initializing DB engine pool.")
    ctx["db_engine"] = create_async_engine(settings.DATABASE_URL, echo=True)
    ctx["session_factory"] = async_sessionmaker(
        bind=ctx["db_engine"],
        class_=AsyncSession,
        expire_on_commit=False
    )

async def shutdown(ctx: dict):
    logger.info("Worker process shutting down... Closing DB engine pool.")
    await ctx["db_engine"].dispose()

async def record_metric(session: AsyncSession, event_type: str):
    """Atomically increments hourly delivery metrics using PostgreSQL ON CONFLICT DO UPDATE."""
    # Truncate current timestamp to the hour (e.g., 14:23:45 -> 14:00:00)
    hourly_timestamp = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    # Prepare atomic PostgreSQL upsert statement
    stmt = insert(NotificationMetrics).values(
        event_type=event_type,
        timestamp=hourly_timestamp,
        count=1
    )
    
    # On unique/primary conflict, increment existing count
    stmt = stmt.on_conflict_do_update(
        index_elements=["event_type", "timestamp"],
        set_={
            "count": NotificationMetrics.count + 1,
            "updated_at": datetime.utcnow()
        }
    )
    await session.execute(stmt)

async def process_notification_task(ctx: dict, notification_id: int):
    logger.info(f"Worker picked up task for Notification ID: {notification_id}")
    
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalars().first()
        
        if not notification:
            logger.error(f"Notification ID {notification_id} not found.")
            return

        notification.status = NotificationStatus.PROCESSING
        await session.commit()

        # Simulate heavy processing operation
        await asyncio.sleep(3)

        notification.status = NotificationStatus.COMPLETED
        await session.commit()

        # Record atomic aggregate metric inside PostgreSQL
        await record_metric(session, event_type="completed")
        await session.commit()
        
        logger.info(f"Notification ID {notification_id} successfully processed and metric recorded!")

class WorkerSettings:
    functions = [process_notification_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT
    )