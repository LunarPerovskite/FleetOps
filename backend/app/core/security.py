"""Security middleware and utilities for FleetOps

CSP, CORS, CSRF, XSS protection, security headers
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import hashlib
import os
from typing import Optional, List

from app.core.config import settings

# ═══════════════════════════════════════
# CONFIGURABLE SECURITY SETTINGS
# ═══════════════════════════════════════

# CORS origins - configurable via environment
CORS_ALLOW_ORIGINS = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8000"
).split(",")

# Trusted hosts - configurable via environment
TRUSTED_HOSTS = os.getenv(
    "TRUSTED_HOSTS",
    "localhost,*.fleetops.local"
).split(",")

# Rate limit per minute
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

# HSTS max age (disabled in DEBUG)
HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))

# CSP policy
CSP_POLICY = os.getenv(
    "CSP_POLICY",
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
    "font-src 'self' data:; connect-src 'self' https:; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self';"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = CSP_POLICY

        # XSS Protection
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (HTTPS Strict Transport Security) - only in production
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"
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
    """CSRF protection for state-changing requests

    Double-Submit Cookie pattern with JWT awareness:
    - Requests with valid Authorization header skip CSRF (JWT bearer auth)
    - Cookie-based requests must provide matching CSRF token
    """

    SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")

    async def dispatch(self, request: Request, call_next):
        # Skip for safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF for JWT-based authentication (Authorization header present)
        if request.headers.get("Authorization"):
            return await call_next(request)

        # Check CSRF token for cookie-based authentication
        csrf_token = request.headers.get("X-CSRF-Token")
        csrf_cookie = request.cookies.get("csrf_token")

        if not csrf_token or not csrf_cookie:
            return Response(
                content='{"error": "CSRF token missing", "hint": "Include X-CSRF-Token header or Authorization header"}',
                status_code=403,
                headers={"Content-Type": "application/json"}
            )

        # Validate CSRF token
        expected = hashlib.sha256(csrf_cookie.encode()).hexdigest()
        if not secrets.compare_digest(csrf_token.encode(), expected.encode()):
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
    origins = [o.strip() for o in CORS_ALLOW_ORIGINS if o.strip()]
    if settings.DEBUG:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,
    )

    # Trusted hosts
    hosts = [h.strip() for h in TRUSTED_HOSTS if h.strip()]
    if settings.DEBUG:
        hosts = ["*"]

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=hosts
    )

    # Note: CSRF and RateLimit middleware require Redis
    # They're added separately after Redis is initialized

def generate_csrf_token():
    """Generate a new CSRF token (token + hashed form)"""
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()

# ═══════════════════════════════════════
# PASSWORD HASHING — Delegated to auth.py
# ═══════════════════════════════════════

from app.core.auth import get_password_hash, verify_password as _auth_verify_password

def hash_password(password: str) -> str:
    """Hash password using bcrypt (delegated to auth module)

    Returns bcrypt format: $2b$12$salt$hash
    """
    return get_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash (delegated to auth module)"""
    return _auth_verify_password(password, hashed)

# ═══════════════════════════════════════
# INPUT SANITIZATION
# ═══════════════════════════════════════

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    import html
    return html.escape(text.strip())
