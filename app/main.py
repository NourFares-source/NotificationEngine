import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from arq.connections import ArqRedis
from app.queue import get_redis_pool
from app.database import get_db
from app.models import Notification, NotificationMetrics
from app.schemas import NotificationCreate, NotificationResponse

redis_pool: ArqRedis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool
    redis_pool = await get_redis_pool()
    yield
    await redis_pool.close()

app = FastAPI(title="Notification & Alert Engine", lifespan=lifespan)

@app.get("/health")
async def health_check():
    redis_alive = await redis_pool.ping()
    return {
        "status": "healthy",
        "services": {
            "web": "online",
            "redis": "connected" if redis_alive else "disconnected"
        }
    }

@app.post("/notifications", status_code=status.HTTP_202_ACCEPTED, response_model=NotificationResponse)
async def send_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    notification = Notification(
        recipient=payload.recipient,
        message=payload.message
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    await redis_pool.enqueue_job("process_notification_task", notification.id)
    return notification

@app.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification_status(
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalars().first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    return notification

@app.get("/analytics/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    cache_key = "analytics:summary"

    # 1. CHECK CACHE (Redis)
    cached_data = await redis_pool.get(cache_key)
    if cached_data:
        return {
            "source": "cache",
            "data": json.loads(cached_data)
        }

    # 2. CACHE MISS: Query PostgreSQL Metrics Table
    result = await db.execute(
        select(
            NotificationMetrics.event_type,
            func.sum(NotificationMetrics.count).label("total_count")
        ).group_by(NotificationMetrics.event_type)
    )
    metrics = result.all()
    
    summary_data = {row.event_type: row.total_count for row in metrics}

    # 3. SET CACHE (Redis with 60-second TTL)
    await redis_pool.set(cache_key, json.dumps(summary_data),ex=60)
    

    return {
        "source": "database",
        "data": summary_data
    }
    
"""
[ Client ] 
   │
   │ 1. POST /notifications
   ▼
[ FastAPI Endpoint: send_notification ]
   │
   ├── 2. await db.commit() ──────────────► [ PostgreSQL ] (Creates row with ID #1, Status: PENDING)
   ├── 3. await db.refresh() ─────────────► [ PostgreSQL ] (Fetches generated ID #1)
   ├── 4. await enqueue_job(..., id=1) ──► [ Redis Queue ] (Pushes job payload to queue)
   │
   │ 5. Returns 202 Accepted (Client gets response in ~10ms!)
   ▼
[ Client receives response ]

-------------------------------------------------------------------------------------------
(Meanwhile, running asynchronously in the background...)

[ Arq Worker: process_notification_task ]
   │
   ├── 1. Pops job (id=1) from [ Redis Queue ]
   ├── 2. Queries PostgreSQL for ID #1
   ├── 3. Updates status to PROCESSING in [ PostgreSQL ]
   ├── 4. Simulates heavy work / sends email (takes 3 seconds)
   └── 5. Updates status to COMPLETED in [ PostgreSQL ]
   
"""