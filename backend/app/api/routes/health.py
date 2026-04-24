"""Health check endpoints for FleetOps

System status, readiness, and liveness probes
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.auth import verify_token
from app.core.metrics import get_metrics_text

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check - always returns 200 if server is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "fleetops-api",
        "version": "0.1.0"
    }


@router.get("/metrics")
def metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""
    return Response(
        content=get_metrics_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - verifies database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "connected",
                "api": "running"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": f"error: {str(e)}",
                "api": "running"
            }
        }


@router.get("/live")
def liveness_check():
    """Liveness check - for Kubernetes probes"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with all service statuses"""
    checks = {}
    
    # Database check
    try:
        db.execute("SELECT 1")
        checks["database"] = {"status": "ok", "response_time_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}
    
    # Redis check (if configured)
    try:
        from app.core.cache import cache
        import asyncio
        
        if cache.redis:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(cache.redis.ping())
            checks["redis"] = {"status": "ok" if result else "error"}
        else:
            checks["redis"] = {"status": "not_configured"}
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}
    
    # Check overall status
    all_ok = all(c["status"] == "ok" for c in checks.values())
    
    return {
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
