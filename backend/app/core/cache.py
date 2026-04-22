"""Redis caching layer for FleetOps

Cache frequently accessed data to reduce database load
"""

import json
import hashlib
from typing import Optional, Any
from functools import wraps
import redis.asyncio as redis
from app.core.config import settings

class CacheManager:
    """Unified cache manager"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.default_ttl = 300  # 5 minutes
    
    async def connect(self):
        """Connect to Redis"""
        if not self.redis:
            try:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=0,
                    decode_responses=True
                )
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        if not self.redis:
            return
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(
                key,
                ttl or self.default_ttl,
                serialized
            )
        except Exception:
            pass
    
    async def delete(self, key: str):
        """Delete from cache"""
        if not self.redis:
            return
        
        try:
            await self.redis.delete(key)
        except Exception:
            pass
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern"""
        if not self.redis:
            return
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception:
            pass
    
    async def get_or_set(self, key: str, fetch_func, ttl: int = None):
        """Get from cache or fetch and store"""
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        value = await fetch_func()
        if value is not None:
            await self.set(key, value, ttl)
        
        return value

# Global cache instance
cache = CacheManager()

# Cache decorators
def cached(prefix: str, ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key_parts = [prefix]
            cache_key = f"{':'.join(key_parts)}:{hashlib.md5(str(args[1:]).encode()).hexdigest()}"
            
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(prefix: str):
    """Decorator to invalidate cache after function call"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await cache.invalidate_pattern(f"{prefix}:*")
            return result
        return wrapper
    return decorator
