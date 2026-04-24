"""Structured logging for FleetOps

Replaces basic logging with structured JSON logs + trace IDs.
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "org_id"):
            log_data["org_id"] = record.org_id
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith("_"):
                try:
                    json.dumps(value)  # Test if serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    handlers: Optional[list] = None
) -> None:
    """Setup structured logging for FleetOps"""
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with FleetOps configuration"""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding fields to logs"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra = kwargs
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra={**self.extra, **kwargs})
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra={**self.extra, **kwargs})
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra={**self.extra, **kwargs})
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra={**self.extra, **kwargs})


# Convenience functions
def log_agent_action(
    agent_id: str,
    action: str,
    task_id: Optional[str] = None,
    details: Optional[Dict] = None
):
    """Log an agent action"""
    logger = get_logger("fleetops.agent")
    logger.info(
        f"Agent {agent_id}: {action}",
        extra={
            "agent_id": agent_id,
            "action": action,
            "task_id": task_id,
            "details": details or {}
        }
    )


def log_cost_event(
    provider: str,
    model: str,
    cost_usd: float,
    tokens_in: int,
    tokens_out: int,
    task_id: Optional[str] = None
):
    """Log a cost event"""
    logger = get_logger("fleetops.cost")
    logger.info(
        f"Cost: ${cost_usd:.6f} for {provider}/{model}",
        extra={
            "provider": provider,
            "model": model,
            "cost_usd": cost_usd,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "task_id": task_id,
            "total_tokens": tokens_in + tokens_out
        }
    )


def log_security_event(
    event_type: str,
    severity: str,
    details: Dict[str, Any],
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Log a security event"""
    logger = get_logger("fleetops.security")
    log_func = getattr(logger, severity.lower(), logger.info)
    log_func(
        f"Security: {event_type}",
        extra={
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details
        }
    )


def log_provider_call(
    provider: str,
    model: str,
    status: str,
    duration_ms: float,
    task_id: Optional[str] = None,
    error: Optional[str] = None
):
    """Log an external provider call"""
    logger = get_logger("fleetops.provider")
    logger.info(
        f"Provider call: {provider}/{model} - {status}",
        extra={
            "provider": provider,
            "model": model,
            "status": status,
            "duration_ms": duration_ms,
            "task_id": task_id,
            "error": error
        }
    )
