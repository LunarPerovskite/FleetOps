from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Approval, User, Task
import uuid

router = APIRouter()

@router.get("/")
async def list_approvals(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Approval).join(Task).where(Task.org_id == current_user.org_id)
    if task_id:
        query = query.where(Approval.task_id == task_id)
    if status:
        query = query.where(Approval.decision == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/pending")
async def get_pending_approvals(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Approval).join(Task).where(
            and_(Task.org_id == current_user.org_id, Approval.decision == None)
        )
    )
    return result.scalars().all()
