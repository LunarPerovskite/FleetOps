"""Standardized error handling for FleetOps

All errors should use these classes for consistent API responses.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class FleetOpsError(Exception):
    """Base error class for all FleetOps errors"""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.trace_id = trace_id
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
                "trace_id": self.trace_id
            }
        }
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()["error"]
        )


# ─── 4xx Client Errors ─────────────────────────────────────────────────

class ValidationError(FleetOpsError):
    """Invalid input data"""
    def __init__(self, message: str, details: Optional[Dict] = None, **kwargs):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
            **kwargs
        )

class AuthenticationError(FleetOpsError):
    """Invalid or missing authentication"""
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            **kwargs
        )

class AuthorizationError(FleetOpsError):
    """Insufficient permissions"""
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            **kwargs
        )

class NotFoundError(FleetOpsError):
    """Resource not found"""
    def __init__(self, resource: str, resource_id: Optional[str] = None, **kwargs):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} '{resource_id}' not found"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id},
            **kwargs
        )

class RateLimitError(FleetOpsError):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60, **kwargs):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
            **kwargs
        )

class ConflictError(FleetOpsError):
    """Resource conflict (e.g., duplicate)"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            **kwargs
        )


# ─── 5xx Server Errors ─────────────────────────────────────────────────

class InternalError(FleetOpsError):
    """Generic internal server error"""
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            status_code=500,
            **kwargs
        )

class ProviderError(FleetOpsError):
    """External LLM provider error"""
    def __init__(
        self,
        provider: str,
        message: str,
        provider_status_code: Optional[int] = None,
        **kwargs
    ):
        details = {"provider": provider}
        if provider_status_code:
            details["provider_status_code"] = provider_status_code
        super().__init__(
            message=f"{provider} error: {message}",
            code="PROVIDER_ERROR",
            status_code=502,
            details=details,
            **kwargs
        )

class ProviderRateLimitError(ProviderError):
    """Provider rate limit (not our rate limit)"""
    def __init__(self, provider: str, retry_after: Optional[int] = None, **kwargs):
        details = {"provider": provider}
        if retry_after:
            details["retry_after"] = retry_after
        FleetOpsError.__init__(
            self,
            message=f"{provider} rate limit exceeded",
            code="PROVIDER_RATE_LIMIT",
            status_code=502,
            details=details,
            **kwargs
        )

class ProviderTimeoutError(ProviderError):
    """Provider timeout"""
    def __init__(self, provider: str, timeout_seconds: int, **kwargs):
        super().__init__(
            provider=provider,
            message=f"Request timed out after {timeout_seconds}s",
            code="PROVIDER_TIMEOUT",
            status_code=504,
            details={"timeout_seconds": timeout_seconds},
            **kwargs
        )

class CircuitBreakerOpenError(FleetOpsError):
    """Circuit breaker is open"""
    def __init__(self, service: str, retry_after: int = 30, **kwargs):
        super().__init__(
            message=f"Service '{service}' is temporarily unavailable. Retry after {retry_after}s.",
            code="CIRCUIT_BREAKER_OPEN",
            status_code=503,
            details={"service": service, "retry_after": retry_after},
            **kwargs
        )

class DatabaseError(FleetOpsError):
    """Database error"""
    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            **kwargs
        )

class BudgetExceededError(FleetOpsError):
    """Budget limit exceeded"""
    def __init__(
        self,
        budget_limit: float,
        current_spend: float,
        resource_type: str = "organization",
        **kwargs
    ):
        super().__init__(
            message=f"Budget exceeded: ${current_spend:.2f} / ${budget_limit:.2f}",
            code="BUDGET_EXCEEDED",
            status_code=402,
            details={
                "budget_limit": budget_limit,
                "current_spend": current_spend,
                "resource_type": resource_type,
                "overage": current_spend - budget_limit
            },
            **kwargs
        )


# ─── Helper Functions ────────────────────────────────────────────────────

def handle_error(error: Exception, trace_id: Optional[str] = None) -> Dict[str, Any]:
    """Convert any exception to a standardized error response"""
    if isinstance(error, FleetOpsError):
        if trace_id and not error.trace_id:
            error.trace_id = trace_id
        return error.to_dict()
    
    # Unknown error - wrap in InternalError
    internal = InternalError(
        message=str(error),
        trace_id=trace_id
    )
    return internal.to_dict()


def error_response(
    code: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized error response dict"""
    return {
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "details": details or {},
            "trace_id": trace_id
        }
    }
