from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Task, Agent, LLMUsage, User, Event

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

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    
    # Tasks completed today
    today = datetime.utcnow().date()
    tasks_completed_today = await db.execute(
        select(func.count(Task.id)).where(
            Task.org_id == current_user.org_id,
            Task.status == "completed",
            Task.completed_at >= today
        )
    )
    
    # Total tasks
    total_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.org_id == current_user.org_id)
    )
    
    # Total agents
    total_agents = await db.execute(
        select(func.count(Agent.id)).where(Agent.org_id == current_user.org_id)
    )
    
    # Cost today
    cost_today = await db.execute(
        select(func.sum(LLMUsage.cost)).where(
            LLMUsage.org_id == current_user.org_id,
            LLMUsage.timestamp >= today
        )
    )
    
    # Success rate (completed / total)
    total_count = total_tasks.scalar() or 0
    completed_count = tasks_completed_today.scalar() or 0
    success_rate = (completed_count / total_count * 100) if total_count > 0 else 0.0
    
    return {
        "active_agents": active_agents.scalar() or 0,
        "tasks_in_progress": tasks_progress.scalar() or 0,
        "pending_approvals": pending_approvals.scalar() or 0,
        "cost_today": cost_today.scalar() or 0.0,
        "tasks_completed_today": completed_count,
        "success_rate": round(success_rate, 1),
        "total_tasks": total_count,
        "total_agents": total_agents.scalar() or 0
    }

@router.get("/activity")
async def get_recent_activity(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get recent events - filter by user_id since org_id is not on Event
    result = await db.execute(
        select(Event).where(
            Event.user_id == current_user.id
        ).order_by(Event.timestamp.desc()).limit(50)
    )
    events = result.scalars().all()
    
    activity = []
    for event in events:
        activity.append({
            "id": str(event.id),
            "type": event.event_type or "event_occurred",
            "description": f"Event: {event.event_type}",
            "timestamp": event.timestamp.isoformat() if event.timestamp else datetime.utcnow().isoformat(),
            "user": event.user_id,
            "agent": event.agent_id,
            "metadata": event.data or {}
        })
    
    return activity
