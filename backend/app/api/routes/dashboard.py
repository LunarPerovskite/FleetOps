from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Task, Agent, LLMUsage, User

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Active agents
    active_agents = await db.execute(
        select(func.count(Agent.id)).where(Agent.org_id == current_user.org_id, Agent.status == "active")
    )
    
    # Tasks in progress
    tasks_progress = await db.execute(
        select(func.count(Task.id)).where(Task.org_id == current_user.org_id, Task.status == "executing")
    )
    
    # Pending approvals
    pending_approvals = await db.execute(
        select(func.count(Task.id)).where(Task.org_id == current_user.org_id, Task.status == "approval_pending")
    )
    
    # Cost today
    today = datetime.utcnow().date()
    cost_today = await db.execute(
        select(func.sum(LLMUsage.cost)).where(
            LLMUsage.org_id == current_user.org_id,
            LLMUsage.timestamp >= today
        )
    )
    
    return {
        "active_agents": active_agents.scalar() or 0,
        "tasks_in_progress": tasks_progress.scalar() or 0,
        "pending_approvals": pending_approvals.scalar() or 0,
        "cost_today": cost_today.scalar() or 0.0
    }
