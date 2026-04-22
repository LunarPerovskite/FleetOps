"""Health check utilities for FleetOps

Check connectivity to all dependent services
"""

import asyncio
from typing import Dict
import asyncpg
from redis import Redis
from app.core.config import settings
from app.core.database import sync_engine
from sqlalchemy import text

async def check_database() -> Dict:
    """Check PostgreSQL connectivity"""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""))
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        return {
            "status": "healthy",
            "type": "postgresql",
            "version": version
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(e)
        }

def check_database_sync() -> Dict:
    """Check PostgreSQL connectivity (synchronous)"""
    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            return {
                "status": "healthy",
                "type": "postgresql",
                "version": version
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(e)
        }

async def check_redis() -> Dict:
    """Check Redis connectivity"""
    try:
        redis = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=5)
        info = redis.info()
        redis.close()
        return {
            "status": "healthy",
            "type": "redis",
            "version": info.get("redis_version", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "type": "redis",
            "error": str(e)
        }

async def check_all() -> Dict:
    """Run all health checks"""
    db_health = await check_database()
    redis_health = await check_redis()
    
    overall = "healthy" if all(
        h["status"] == "healthy" 
        for h in [db_health, redis_health]
    ) else "degraded"
    
    if any(h["status"] == "unhealthy" for h in [db_health, redis_health]):
        overall = "unhealthy"
    
    return {
        "status": overall,
        "services": {
            "database": db_health,
            "redis": redis_health,
            "api": {"status": "healthy", "type": "fastapi"}
        },
        "timestamp": asyncio.get_event_loop().time()
    }
