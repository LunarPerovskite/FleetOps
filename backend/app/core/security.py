"""Security middleware and utilities for FleetOps

CSP, CORS, CSRF, XSS protection, security headers
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import hashlib
from typing import Optional

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # XSS Protection
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (HTTPS Strict Transport Security)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Remove server identification
        response.headers.pop("Server", None)
        
        return response

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip for GET, HEAD, OPTIONS
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)
        
        # Check CSRF token for state-changing requests
        csrf_token = request.headers.get("X-CSRF-Token")
        csrf_cookie = request.cookies.get("csrf_token")
        
        if not csrf_token or not csrf_cookie:
            return Response(
                content='{"error": "CSRF token missing"}',
                status_code=403,
                headers={"Content-Type": "application/json"}
            )
        
        # Validate CSRF token
        expected = hashlib.sha256(csrf_cookie.encode()).hexdigest()
        if not secrets.compare_digest(csrf_token, expected):
            return Response(
                content='{"error": "Invalid CSRF token"}',
                status_code=403,
                headers={"Content-Type": "application/json"}
            )
        
        return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client
        self.requests = {}  # Fallback if no Redis
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.headers.get("X-Forwarded-For", 
                                       request.client.host if request.client else "unknown")
        
        # Check rate limit
        if self.redis:
            key = f"rate_limit:{client_ip}"
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, 60)  # 1 minute window
            
            if current > 100:  # 100 requests per minute
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    headers={
                        "Content-Type": "application/json",
                        "Retry-After": "60"
                    }
                )
        
        return await call_next(request)

def setup_security(app):
    """Configure all security middleware"""
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://*.vercel.app",
            "https://*.railway.app"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,
    )
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "*.vercel.app",
            "*.railway.app",
            "*.fleetops.io"
        ]
    )
    
    # Note: CSRF and RateLimit middleware require Redis
    # They're added separately after Redis is initialized

def generate_csrf_token():
    """Generate a new CSRF token"""
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        salt, stored_hash = hashed.split("$")
        hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(hash.hex(), stored_hash)
    except ValueError:
        return False

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    import html
    return html.escape(text.strip())
