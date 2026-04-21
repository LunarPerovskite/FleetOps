from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Task, Agent, User, TaskStatus, RiskLevel, Event
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/")
async def create_task(
    title: str,
    description: Optional[str] = None,
    agent_id: Optional[str] = None,
    risk_level: RiskLevel = RiskLevel.LOW,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        agent_id=agent_id,
        risk_level=risk_level,
        created_by=current_user.id,
        org_id=current_user.org_id,
        stage="initiation"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.get("/")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task).where(Task.org_id == current_user.org_id)
    if status:
        query = query.where(Task.status == status)
    if agent_id:
        query = query.where(Task.agent_id == agent_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Task).where(and_(Task.id == task_id, Task.org_id == current_user.org_id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/{task_id}/approve")
async def approve_task_stage(
    task_id: str,
    decision: str,  # approve, reject, request_changes, escalate
    comments: Optional[str] = None,
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
        decision=decision,
        comments=comments
    )
    db.add(approval)
    
    # Update task stage based on decision
    if decision == "approve":
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
    elif decision == "reject":
        task.status = TaskStatus.FAILED
    elif decision == "escalate":
        # Escalate to next human level
        pass
    
    await db.commit()
    return {"status": "success", "task_id": task_id, "new_stage": task.stage}
