from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Event, User

router = APIRouter()

@router.post("/")
async def create_event(
    event_type: str,
    data: dict,
    task_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import hashlib
    event_data = {
        "event_type": event_type,
        "task_id": task_id,
        "agent_id": agent_id,
        "user_id": current_user.id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    signature = hashlib.sha256(str(event_data).encode()).hexdigest()
    
    event = Event(
        id=signature[:64],
        event_type=event_type,
        task_id=task_id,
        agent_id=agent_id,
        user_id=current_user.id,
        data=data,
        signature=signature,
        timestamp=datetime.utcnow()
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

@router.get("/")
async def list_events(
    task_id: Optional[str] = None,
    event_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models import Task
    query = select(Event).join(Task).where(Task.org_id == current_user.org_id)
    
    if task_id:
        query = query.where(Event.task_id == task_id)
    if event_type:
        query = query.where(Event.event_type == event_type)
    if agent_id:
        query = query.where(Event.agent_id == agent_id)
    if start_date:
        query = query.where(Event.timestamp >= start_date)
    if end_date:
        query = query.where(Event.timestamp <= end_date)
    
    query = query.order_by(Event.timestamp.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.models import Task
    result = await db.execute(
        select(Event).join(Task).where(and_(Event.id == event_id, Task.org_id == current_user.org_id))
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
