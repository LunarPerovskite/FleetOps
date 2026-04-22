"""Structured Logging Configuration for FleetOps

JSON logging with correlation IDs
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

class JSONFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": correlation_id.get() or str(uuid.uuid4()),
            "thread": record.thread,
            "process": record.process
        }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get structured logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for current context"""
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid

def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id.get() or ""

class CorrelationIdMiddleware:
    """FastAPI middleware to set correlation ID"""
    
    async def __call__(self, request, call_next):
        # Get or generate correlation ID
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(cid)
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        
        return response

def log_event(event_type: str, data: Dict[str, Any],
             logger: logging.Logger = None):
    """Log structured event"""
    if logger is None:
        logger = get_logger("fleetops.events")
    
    extra = {
        "event_type": event_type,
        "data": data,
        "correlation_id": get_correlation_id()
    }
    
    logger.info(f"Event: {event_type}", extra={"extra": extra})

def log_error(error: Exception, context: Dict[str, Any] = None,
             logger: logging.Logger = None):
    """Log structured error"""
    if logger is None:
        logger = get_logger("fleetops.errors")
    
    extra = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
        "correlation_id": get_correlation_id()
    }
    
    logger.error(f"Error: {type(error).__name__}", exc_info=True,
                extra={"extra": extra})

# Initialize root logger
root_logger = get_logger("fleetops")
