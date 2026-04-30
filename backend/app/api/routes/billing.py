"""Billing API for FleetOps (Self-Hosted)

Track usage for self-hosted installations. No cloud billing.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.core.database import get_sync_db
from app.api.routes.auth import get_current_user
from app.models.models import User, Task, Agent, Organization

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/usage")
def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """Get current usage statistics for self-hosted"""
    org_id = current_user.org_id
    
    # Calculate start of month
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count metrics
    tasks_this_month = db.query(Task).filter(
        Task.org_id == org_id,
        Task.created_at >= start_of_month
    ).count()
    
    tasks_total = db.query(Task).filter(Task.org_id == org_id).count()
    
    agents_active = db.query(Agent).filter(
        Agent.org_id == org_id,
        Agent.status == "active"
    ).count()
    
    agents_total = db.query(Agent).filter(Agent.org_id == org_id).count()
    
    # Get org details
    org = db.query(Organization).filter(Organization.id == org_id).first()
    team_members = 1  # In production, count actual team members
    
    return {
        "tasks_this_month": tasks_this_month,
        "tasks_total": tasks_total,
        "agents_active": agents_active,
        "agents_total": agents_total,
        "team_members": team_members,
        "api_calls": 0,  # In production, track from middleware
        "storage_gb": 0.5,  # Estimated
        "period": {
            "start": start_of_month.isoformat(),
            "end": now.isoformat()
        },
        "deployment": "self_hosted",
        "license": "MIT"
    }

@router.get("/history")
def get_billing_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """Get usage history (self-hosted has no billing)"""
    return {
        "message": "Self-hosted FleetOps is free. No billing history.",
        "invoices": [
            {
                "id": "self_hosted",
                "date": datetime.utcnow().isoformat(),
                "amount": 0,
                "plan": "self_hosted",
                "status": "active",
                "description": "MIT License — unlimited, free, open source"
            }
        ]
    }

@router.get("/tiers")
def get_tiers():
    """Get available tiers (only self-hosted for now)"""
    return {
        "message": "FleetOps is currently self-hosted only.",
        "tiers": [
            {
                "id": "self_hosted",
                "name": "Self-Hosted",
                "price": 0,
                "price_monthly": 0,
                "description": "Run on your own infrastructure",
                "features": [
                    "Unlimited users",
                    "Unlimited tasks",
                    "Unlimited agents",
                    "All features included",
                    "Full API access",
                    "Community support",
                    "MIT License"
                ],
                "cta": "Free Forever",
                "popular": True
            }
        ],
        "note": "Cloud hosting may be available in the future. For now, self-hosted is the only option and is completely free."
    }
