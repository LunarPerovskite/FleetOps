"""Rate Limiter for FleetOps API

Features:
- Per-user rate limiting
- Per-org rate limiting
- Different tiers (free, pro, business, enterprise)
- Redis-based sliding window
"""

import time
from datetime import datetime
from typing import Optional, Dict
import redis
from fastapi import HTTPException, Request

from app.core.config import settings

class RateLimiter:
    """API rate limiter with tier-based limits"""
    
    # Rate limits per tier (requests per minute)
    TIER_LIMITS = {
        "free": 60,
        "pro": 300,
        "business": 1000,
        "enterprise": 5000
    }
    
    def __init__(self):
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=1,  # Use different DB for rate limiting
                decode_responses=True
            )
        except:
            self.redis = None
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> Dict:
        """Check if request is allowed under rate limit"""
        if not self.redis:
            return {"allowed": True, "remaining": limit}
        
        now = time.time()
        window_start = now - window
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current = self.redis.zcard(key)
        
        if current >= limit:
            # Get time until reset
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            reset_time = oldest[0][1] + window if oldest else now + window
            
            return {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_at": reset_time,
                "retry_after": max(1, int(reset_time - now))
            }
        
        # Add current request
        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, window)
        
        return {
            "allowed": True,
            "limit": limit,
            "remaining": limit - current - 1,
            "reset_at": now + window
        }
    
    def check_user_limit(self, user_id: str, tier: str = "free") -> Dict:
        """Check rate limit for user"""
        limit = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])
        key = f"rate_limit:user:{user_id}"
        return self.is_allowed(key, limit)
    
    def check_org_limit(self, org_id: str, tier: str = "free") -> Dict:
        """Check rate limit for organization"""
        limit = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"]) * 5
        key = f"rate_limit:org:{org_id}"
        return self.is_allowed(key, limit)
    
    def check_ip_limit(self, ip: str) -> Dict:
        """Check rate limit for IP address"""
        limit = 100  # Stricter for IPs
        key = f"rate_limit:ip:{ip}"
        return self.is_allowed(key, limit)

# Global rate limiter
rate_limiter = RateLimiter()

async def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting"""
    user = getattr(request.state, "user", None)
    user_id = user.id if user else None
    tier = getattr(user, "tier", "free") if user else "free"
    
    # Check IP limit first
    ip = request.client.host
    ip_result = rate_limiter.check_ip_limit(ip)
    
    if not ip_result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "type": "ip",
                "retry_after": ip_result["retry_after"]
            },
            headers={"Retry-After": str(ip_result["retry_after"])}
        )
    
    # Check user limit
    if user_id:
        user_result = rate_limiter.check_user_limit(user_id, tier)
        
        if not user_result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "type": "user",
                    "retry_after": user_result["retry_after"]
                },
                headers={"Retry-After": str(user_result["retry_after"])}
            )
    
    return True
