from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.pagination import PaginationParams, paginate_query
from app.api.routes.auth import get_current_user
from app.models.models import Task, Agent, User, TaskStatus, RiskLevel, Event
import uuid
from datetime import datetime

router = APIRouter()

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    agent_id: Optional[str] = None
    risk_level: str = "low"

@router.post("/")
async def create_task(
    data: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    risk_map = {
        "low": RiskLevel.LOW,
        "medium": RiskLevel.MEDIUM,
        "high": RiskLevel.HIGH,
        "critical": RiskLevel.CRITICAL
    }
    task = Task(
        id=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        agent_id=data.agent_id,
        risk_level=risk_map.get(data.risk_level, RiskLevel.LOW),
        created_by=current_user.id,
        org_id=current_user.org_id,
        created_at=datetime.utcnow()
    )
    db.add(task)
    await db.commit()
    return task

@router.get("/")
async def list_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tasks with pagination"""
    # Build query
    query = select(Task).where(Task.org_id == current_user.org_id)
    
    if status:
        query = query.where(Task.status == status)
    if agent_id:
        query = query.where(Task.agent_id == agent_id)
    
    query = query.order_by(Task.created_at.desc())
    
    # Get total count
    count_query = select(func.count(Task.id)).where(Task.org_id == current_user.org_id)
    if status:
        count_query = count_query.where(Task.status == status)
    if agent_id:
        count_query = count_query.where(Task.agent_id == agent_id)
    
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    count_result = await db.execute(count_query)
    
    items = result.scalars().all()
    total = count_result.scalar()
    pages = (total + page_size - 1) // page_size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }

@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(and_(Task.id == task_id, Task.org_id == current_user.org_id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

@router.put("/{task_id}")
async def update_task(
    task_id: str,
    data: UpdateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(and_(Task.id == task_id, Task.org_id == current_user.org_id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if data.title:
        task.title = data.title
    if data.description:
        task.description = data.description
    if data.status:
        task.status = data.status
    task.updated_at = datetime.utcnow()
    
    await db.commit()
    return task

class ApproveTaskRequest(BaseModel):
    decision: str
    comments: Optional[str] = None

@router.post("/{task_id}/approve")
async def approve_task_stage(
    task_id: str,
    data: ApproveTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(and_(Task.id == task_id, Task.org_id == current_user.org_id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create approval event
    from app.models.models import Approval
    approval = Approval(
        id=str(uuid.uuid4()),
        task_id=task_id,
        human_id=current_user.id,
        stage=task.stage,
        decision=data.decision,
        comments=data.comments
    )
    db.add(approval)

    # Update task stage based on decision
    if data.decision == "approve":
        if task.stage == "initiation":
            task.stage = "planning"
            task.status = TaskStatus.PLANNING
        elif task.stage == "planning":
            task.stage = "execution"
            task.status = TaskStatus.EXECUTING
        elif task.stage == "execution":
            task.stage = "review"
            task.status = TaskStatus.REVIEWING
        elif task.stage == "review":
            task.stage = "external_action"
            task.status = TaskStatus.APPROVAL_PENDING
        elif task.stage == "external_action":
            task.stage = "delivery"
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
    elif data.decision == "reject":
        task.status = TaskStatus.FAILED
    elif data.decision == "escalate":
        # Escalate to next human level
        pass
    
    await db.commit()
    return {"status": "success", "task_id": task_id, "new_stage": task.stage}

@router.get("/{task_id}/events")
async def get_task_events(
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get events for a specific task with pagination"""
    # Join via Task.org_id since Event has no org_id column
    query = select(Event).join(Task).where(
        and_(Event.task_id == task_id, Task.org_id == current_user.org_id)
    ).order_by(Event.timestamp.desc())
    
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size
    }
