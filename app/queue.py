from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from app.config import settings

async def get_redis_pool() -> ArqRedis:
    """Creates a Redis connection pool for enqueuing jobs."""
    return await create_pool(
        RedisSettings(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT
        )
    )