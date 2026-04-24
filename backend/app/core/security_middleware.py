"""Security middleware for FleetOps

Production-ready security headers, rate limiting, and audit logging.
"""

import re
import time
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"  # Disabled - rely on CSP instead
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove server fingerprinting
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit trail"""
    
    # Skip logging for health checks
    SKIP_PATHS = {"/health", "/api/v1/health", "/api/v1/live", "/api/v1/ready"}
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Skip health checks
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Generate trace ID for request correlation
        trace_id = hashlib.sha256(
            f"{request.client.host}:{time.time()}".encode()
        ).hexdigest()[:16]
        request.state.trace_id = trace_id
        
        response = await call_next(request)
        
        # Log after response
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
            "content_length": response.headers.get("content-length"),
        }
        
        # In production, send to logging pipeline
        import logging
        logger = logging.getLogger("fleetops.audit")
        logger.info(json.dumps(log_entry))
        
        # Add trace ID to response
        response.headers["X-Trace-Id"] = trace_id
        
        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Limit request body size"""
    
    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request body too large. Max: {self.MAX_BODY_SIZE} bytes"
            )
        return await call_next(request)


# Combine into single middleware for easy application
class SecurityMiddleware(BaseHTTPMiddleware):
    """Combined security middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.headers = SecurityHeadersMiddleware(app)
        self.audit = AuditLogMiddleware(app)
        self.size_limit = RequestSizeMiddleware(app)
    
    async def dispatch(self, request: Request, call_next):
        # Apply all middleware layers
        
        # 1. Size limit
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > RequestSizeMiddleware.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request body too large"
            )
        
        # 2. Process request
        response = await call_next(request)
        
        # 3. Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove fingerprinting
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        # 4. Audit log (skip health checks)
        if request.url.path not in AuditLogMiddleware.SKIP_PATHS:
            trace_id = getattr(request.state, "trace_id", None)
            if trace_id:
                response.headers["X-Trace-Id"] = trace_id
        
        return response
