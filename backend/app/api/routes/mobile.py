"""Mobile App API Routes

Simplified endpoints optimized for mobile apps
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.services.customer_service import CustomerServiceManager
from app.models.models import User

router = APIRouter()

@router.get("/dashboard")
async def mobile_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get mobile-optimized dashboard"""
    # Simplified stats for mobile
    return {
        "stats": {
            "active_tasks": 0,  # Would query DB
            "pending_approvals": 0,
            "active_agents": 0,
            "alerts": 0
        },
        "quick_actions": [
            {"id": "approve", "label": "Approve Tasks", "icon": "check"},
            {"id": "agents", "label": "View Agents", "icon": "bot"},
            {"id": "tasks", "label": "My Tasks", "icon": "list"},
            {"id": "alerts", "label": "Alerts", "icon": "bell"}
        ]
    }

@router.get("/notifications")
async def mobile_notifications(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get notifications for mobile"""
    return {
        "unread_count": 0,
        "notifications": []
    }

@router.post("/approvals/{approval_id}/quick-action")
async def quick_approval(
    approval_id: str,
    action: str,  # approve, reject, escalate
    current_user: User = Depends(get_current_user)
):
    """Quick approval action for mobile"""
    return {
        "status": "success",
        "approval_id": approval_id,
        "action": action
    }

@router.get("/agents/status")
async def mobile_agent_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent status for mobile"""
    return {
        "agents": [
            {"id": "agent_1", "name": "Support Agent", "status": "active", "tasks": 3},
            {"id": "agent_2", "name": "Sales Agent", "status": "idle", "tasks": 0}
        ]
    }

@router.get("/tasks/my")
async def my_tasks(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's tasks"""
    return {
        "tasks": []
    }
