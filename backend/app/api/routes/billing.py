"""Billing API for FleetOps

Track usage and show cost comparison (for cloud upsell)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Task, Agent, Organization

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/usage")
def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current month usage statistics"""
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
    
    # Estimate cloud cost
    if team_members <= 5:
        estimated_cloud_cost = 29
    elif team_members <= 25:
        estimated_cloud_cost = 59
    else:
        estimated_cloud_cost = 99
    
    return {
        "tasks_this_month": tasks_this_month,
        "tasks_total": tasks_total,
        "agents_active": agents_active,
        "agents_total": agents_total,
        "team_members": team_members,
        "api_calls": 0,  # In production, track from middleware
        "storage_gb": 0.5,  # Estimated
        "estimated_cloud_cost": estimated_cloud_cost,
        "self_hosted_cost": 0,
        "savings": estimated_cloud_cost,
        "period": {
            "start": start_of_month.isoformat(),
            "end": now.isoformat()
        }
    }

@router.get("/history")
def get_billing_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing history (for cloud users)"""
    # Return mock history for demo
    return {
        "invoices": [
            {
                "id": "inv_001",
                "date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "amount": 0,
                "plan": "self_hosted",
                "status": "free",
                "description": "Self-hosted — unlimited, free"
            }
        ]
    }

@router.get("/tiers")
def get_tiers():
    """Get pricing tiers"""
    return {
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
                    "Community support"
                ],
                "cta": "Free Forever",
                "popular": False
            },
            {
                "id": "starter",
                "name": "Cloud Starter",
                "price": 29,
                "price_monthly": 29,
                "description": "Managed hosting for small teams",
                "features": [
                    "Up to 5 team members",
                    "Unlimited tasks",
                    "Unlimited agents",
                    "Automatic updates",
                    "Daily backups",
                    "Email support",
                    "Custom domain"
                ],
                "cta": "Start Free Trial",
                "popular": False
            },
            {
                "id": "pro",
                "name": "Cloud Pro",
                "price": 59,
                "price_monthly": 59,
                "description": "For growing teams",
                "features": [
                    "Up to 25 team members",
                    "Everything in Starter",
                    "Priority support",
                    "99.9% uptime SLA",
                    "Advanced analytics"
                ],
                "cta": "Start Free Trial",
                "popular": True
            },
            {
                "id": "business",
                "name": "Cloud Business",
                "price": 99,
                "price_monthly": 99,
                "description": "For large organizations",
                "features": [
                    "Unlimited team members",
                    "Everything in Pro",
                    "Dedicated support",
                    "99.99% uptime SLA",
                    "Custom integrations"
                ],
                "cta": "Contact Sales",
                "popular": False
            }
        ]
    }
