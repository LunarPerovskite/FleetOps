"""Security middleware for FleetOps

- Rate limiting
- Input validation
- Output sanitization
- Security headers
- CORS configuration
"""

import re
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > window_start]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[key].append(now)
        return True

# Global limiters
public_limiter = RateLimiter(max_requests=30, window_seconds=60)   # Stricter
auth_limiter = RateLimiter(max_requests=10, window_seconds=60)      # Login attempts
api_limiter = RateLimiter(max_requests=100, window_seconds=60)      # API usage

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server information
        response.headers.pop("Server", None)
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting"""
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        
        # Different limits for different endpoints
        if path.startswith("/api/v1/auth"):
            limiter = auth_limiter
        elif path.startswith("/api/v1"):
            limiter = api_limiter
        else:
            limiter = public_limiter
        
        if not limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        return await call_next(request)

class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize request inputs"""
    
    SQLI_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter)\b.*?\b(from|into|table|database)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
        r"(\b(waitfor|delay|sleep)\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?<\/script>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Sanitize query parameters
        for key, values in request.query_params.multi_items():
            for pattern in self.SQLI_PATTERNS + self.XSS_PATTERNS:
                if re.search(pattern, str(values), re.IGNORECASE):
                    raise HTTPException(status_code=400, detail="Potentially malicious input detected")
        
        return await call_next(request)

def get_security_config() -> Dict:
    """Get current security configuration status"""
    from app.core.encryption import get_master_key_status
    
    return {
        "encryption": get_master_key_status(),
        "rate_limiting": {
            "public": {"max_requests": 30, "window": "60s"},
            "auth": {"max_requests": 10, "window": "60s"},
            "api": {"max_requests": 100, "window": "60s"},
        },
        "headers": {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "enabled",
        },
        "audit_logging": {
            "enabled": True,
            "immutable": True,
            "chain_verification": True,
        }
    }
