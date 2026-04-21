from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime
import uuid

from app.models.models import Task, TaskStatus, RiskLevel, Approval, Event, Agent

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, title: str, description: Optional[str], agent_id: Optional[str], 
                         risk_level: RiskLevel, created_by: str, org_id: str) -> Task:
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            agent_id=agent_id,
            risk_level=risk_level,
            created_by=created_by,
            org_id=org_id,
            status=TaskStatus.CREATED,
            stage="initiation"
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def transition_stage(self, task_id: str, decision: str, human_id: str, comments: Optional[str] = None) -> Task:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Task not found")
        
        # Create approval record
        approval = Approval(
            id=str(uuid.uuid4()),
            task_id=task_id,
            human_id=human_id,
            stage=task.stage,
            decision=decision,
            comments=comments
        )
        self.db.add(approval)
        
        # Stage transitions
        stage_flow = {
            "initiation": "planning",
            "planning": "execution",
            "execution": "review",
            "review": "external_action",
            "external_action": "delivery"
        }
        
        if decision == "approve":
            if task.stage in stage_flow:
                task.stage = stage_flow[task.stage]
                if task.stage == "execution":
                    task.status = TaskStatus.EXECUTING
                elif task.stage == "review":
                    task.status = TaskStatus.REVIEWING
                elif task.stage == "external_action":
                    task.status = TaskStatus.APPROVAL_PENDING
                elif task.stage == "delivery":
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
        elif decision == "reject":
            task.status = TaskStatus.FAILED
        elif decision == "escalate":
            # Mark for escalation
            task.risk_level = RiskLevel.HIGH
        
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def get_task_with_events(self, task_id: str) -> dict:
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None
        
        events_result = await self.db.execute(
            select(Event).where(Event.task_id == task_id).order_by(Event.timestamp.desc())
        )
        events = events_result.scalars().all()
        
        approvals_result = await self.db.execute(
            select(Approval).where(Approval.task_id == task_id).order_by(Approval.created_at.desc())
        )
        approvals = approvals_result.scalars().all()
        
        return {
            "task": task,
            "events": events,
            "approvals": approvals
        }
