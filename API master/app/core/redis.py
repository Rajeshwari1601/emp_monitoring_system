import redis
import redis.asyncio as async_redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

async_redis_client = async_redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    # For live stream bytes, we might NOT want decode_responses=True for the pubsub specifically,
    # but the client itself can have it if used for other things.
    # Actually, for Pub/Sub with binary data, it's better to have a separate client or just use what we need.
)

def get_redis():
    return redis_client

def get_async_redis():
    return async_redis_client
