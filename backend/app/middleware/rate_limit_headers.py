"""Rate Limit Headers Middleware

Add X-RateLimit headers to all responses
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
import time

class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """Add rate limit headers to responses"""
    
    def __init__(self, app, default_limit: int = 100, window: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window = window
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = request.headers.get("X-Forwarded-For", 
                                       request.client.host if request.client else "unknown")
        
        # Clean old requests
        now = time.time()
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < self.window
            ]
        
        # Count current requests
        current_count = len(self.requests.get(client_id, []))
        remaining = max(0, self.default_limit - current_count)
        reset_time = int(now + self.window)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.default_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        response.headers["X-RateLimit-Window"] = str(self.window)
        
        # Add Retry-After if rate limited
        if current_count >= self.default_limit:
            response.headers["Retry-After"] = str(self.window)
        
        # Track this request
        if client_id not in self.requests:
            self.requests[client_id] = []
        self.requests[client_id].append(now)
        
        return response
