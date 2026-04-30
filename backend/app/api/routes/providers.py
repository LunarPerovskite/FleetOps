"""Provider Configuration API for FleetOps

Manage infrastructure provider settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_sync_db
from app.api.routes.auth import get_current_user
from app.models.models import User

router = APIRouter(prefix="/providers", tags=["Providers"])

# Provider definitions
PROVIDERS = {
    "auth": [
        {"id": "clerk", "name": "Clerk", "free_tier": True, "setup_time": "5 min"},
        {"id": "auth0", "name": "Auth0", "free_tier": True, "setup_time": "15 min"},
        {"id": "okta", "name": "Okta", "free_tier": False, "setup_time": "30 min"},
        {"id": "self_hosted", "name": "Self-Hosted", "free_tier": True, "setup_time": "2 hr"},
    ],
    "database": [
        {"id": "supabase", "name": "Supabase", "free_tier": True, "setup_time": "5 min"},
        {"id": "neon", "name": "Neon", "free_tier": True, "setup_time": "5 min"},
        {"id": "aws_rds", "name": "AWS RDS", "free_tier": False, "setup_time": "20 min"},
        {"id": "postgres", "name": "PostgreSQL", "free_tier": True, "setup_time": "30 min"},
    ],
    "hosting": [
        {"id": "vercel", "name": "Vercel", "free_tier": True, "setup_time": "5 min"},
        {"id": "railway", "name": "Railway", "free_tier": True, "setup_time": "10 min"},
        {"id": "aws", "name": "AWS", "free_tier": False, "setup_time": "1 hr"},
    ],
    "secrets": [
        {"id": "env", "name": "Environment Variables", "free_tier": True, "setup_time": "1 min"},
        {"id": "doppler", "name": "Doppler", "free_tier": True, "setup_time": "10 min"},
        {"id": "vault", "name": "HashiCorp Vault", "free_tier": True, "setup_time": "1 hr"},
    ],
    "monitoring": [
        {"id": "sentry", "name": "Sentry", "free_tier": True, "setup_time": "5 min"},
        {"id": "datadog", "name": "Datadog", "free_tier": False, "setup_time": "20 min"},
        {"id": "cloudwatch", "name": "CloudWatch", "free_tier": True, "setup_time": "15 min"},
    ],
}

# Default configuration
DEFAULT_CONFIG = {
    "auth_provider": "clerk",
    "database": "supabase",
    "hosting": "vercel",
    "secrets": "env",
    "monitoring": "sentry",
}

# In-memory storage (use Redis in production)
provider_configs: Dict[str, Dict[str, Any]] = {}

@router.get("/config")
def get_provider_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """Get current provider configuration"""
    org_id = current_user.org_id
    config = provider_configs.get(org_id, DEFAULT_CONFIG.copy())
    return {"config": config, "providers": PROVIDERS}

@router.put("/config")
def update_provider_config(
    config: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """Update provider configuration"""
    org_id = current_user.org_id
    
    # Validate providers
    for key, value in config.items():
        category = key.replace("_provider", "").replace("auth", "auth")
        if category not in PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown category: {category}"
            )
        valid_ids = [p["id"] for p in PROVIDERS[category]]
        if value not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider '{value}' for {category}"
            )
    
    provider_configs[org_id] = config
    return {"config": config, "message": "Configuration updated"}

@router.get("/health")
def check_provider_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """Check health of configured providers"""
    org_id = current_user.org_id
    config = provider_configs.get(org_id, DEFAULT_CONFIG.copy())
    
    statuses = {}
    for key, provider_id in config.items():
        # Simulate health check
        # In production, actually check provider APIs
        statuses[provider_id] = "ok"
    
    return {"statuses": statuses, "overall": "healthy"}

@router.get("/presets")
def get_presets():
    """Get quick start presets"""
    return {
        "easy": {
            "name": "Easiest",
            "description": "Clerk + Vercel + Supabase",
            "config": {
                "auth_provider": "clerk",
                "database": "supabase",
                "hosting": "vercel",
                "secrets": "env",
                "monitoring": "sentry",
            }
        },
        "balanced": {
            "name": "Balanced",
            "description": "Auth0 + Railway + Neon",
            "config": {
                "auth_provider": "auth0",
                "database": "neon",
                "hosting": "railway",
                "secrets": "doppler",
                "monitoring": "sentry",
            }
        },
        "enterprise": {
            "name": "Enterprise",
            "description": "Okta + AWS",
            "config": {
                "auth_provider": "okta",
                "database": "aws_rds",
                "hosting": "aws",
                "secrets": "vault",
                "monitoring": "datadog",
            }
        }
    }
