"""
Redis configuration and connection management
"""

import aioredis
import structlog
from typing import Optional

from app.core.config import settings

logger = structlog.get_logger()

# Global Redis connection
redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def get_redis() -> aioredis.Redis:
    """Get Redis client instance"""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")


class CacheService:
    """Redis cache service with common operations"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            if ttl:
                return await self.redis.setex(key, ttl, value)
            else:
                return await self.redis.set(key, value)
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return await self.redis.delete(key)
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return await self.redis.exists(key)
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error("Cache increment error", key=key, error=str(e))
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error("Cache expire error", key=key, error=str(e))
            return False

