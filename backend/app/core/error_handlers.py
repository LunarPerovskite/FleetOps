"""Global Error Handlers for FleetOps

Centralized exception handling
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback

from app.core.logging_config import log_error, get_correlation_id

class FleetOpsException(Exception):
    """Base exception for FleetOps"""
    def __init__(self, message: str, code: str = None, 
                 status_code: int = 500, details: dict = None):
        self.message = message
        self.code = code or "internal_error"
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class AuthenticationError(FleetOpsException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="auth_error", status_code=401)

class AuthorizationError(FleetOpsException):
    """Not authorized"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, code="forbidden", status_code=403)

class ValidationError(FleetOpsException):
    """Validation failed"""
    def __init__(self, message: str = "Validation error", details: dict = None):
        super().__init__(message, code="validation_error", 
                        status_code=400, details=details)

class NotFoundError(FleetOpsException):
    """Resource not found"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", code="not_found", 
                        status_code=404)

class RateLimitError(FleetOpsException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__("Rate limit exceeded", code="rate_limit", 
                        status_code=429)
        self.retry_after = retry_after

class ConflictError(FleetOpsException):
    """Resource conflict"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, code="conflict", status_code=409)

async def fleetops_exception_handler(request: Request, 
                                     exc: FleetOpsException):
    """Handle FleetOps exceptions"""
    log_error(exc, {
        "path": request.url.path,
        "method": request.method,
        "correlation_id": get_correlation_id()
    })
    
    response = {
        "error": exc.code,
        "message": exc.message,
        "details": exc.details,
        "correlation_id": get_correlation_id()
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )

async def validation_exception_handler(request: Request,
                                     exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": error["loc"][-1] if error["loc"] else "unknown",
            "message": error["msg"],
            "type": error["type"]
        })
    
    log_error(Exception("Validation error"), {
        "path": request.url.path,
        "errors": errors,
        "correlation_id": get_correlation_id()
    })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": {"errors": errors},
            "correlation_id": get_correlation_id()
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    log_error(exc, {
        "path": request.url.path,
        "method": request.method,
        "traceback": traceback.format_exc(),
        "correlation_id": get_correlation_id()
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "correlation_id": get_correlation_id()
        }
    )

# Register handlers
def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    app.add_exception_handler(FleetOpsException, fleetops_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
