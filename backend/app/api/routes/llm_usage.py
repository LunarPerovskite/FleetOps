from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import LLMUsage, User
import uuid

router = APIRouter()

@router.post("/")
async def log_llm_usage(
    provider: str,
    model: str,
    task_id: str,
    agent_id: str,
    tokens_in: int,
    tokens_out: int,
    cost: float,
    latency_ms: int,
    temperature: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    usage = LLMUsage(
        id=str(uuid.uuid4()),
        provider=provider,
        model=model,
        task_id=task_id,
        agent_id=agent_id,
        org_id=current_user.org_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost,
        latency_ms=latency_ms,
        temperature=temperature
    )
    db.add(usage)
    await db.commit()
    await db.refresh(usage)
    return usage

@router.get("/")
async def get_llm_usage(
    agent_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(LLMUsage).where(LLMUsage.org_id == current_user.org_id)
    if agent_id:
        query = query.where(LLMUsage.agent_id == agent_id)
    if start_date:
        query = query.where(LLMUsage.timestamp >= start_date)
    if end_date:
        query = query.where(LLMUsage.timestamp <= end_date)
    
    query = query.order_by(LLMUsage.timestamp.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/stats")
async def get_usage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total cost today
    today = datetime.utcnow().date()
    total_cost = await db.execute(
        select(func.sum(LLMUsage.cost)).where(
            LLMUsage.org_id == current_user.org_id,
            func.date(LLMUsage.timestamp) == today
        )
    )
    
    # Total tokens today
    total_tokens = await db.execute(
        select(func.sum(LLMUsage.tokens_in + LLMUsage.tokens_out)).where(
            LLMUsage.org_id == current_user.org_id,
            func.date(LLMUsage.timestamp) == today
        )
    )
    
    # Cost by model
    cost_by_model = await db.execute(
        select(LLMUsage.model, func.sum(LLMUsage.cost)).where(
            LLMUsage.org_id == current_user.org_id,
            func.date(LLMUsage.timestamp) == today
        ).group_by(LLMUsage.model)
    )
    
    return {
        "total_cost_today": total_cost.scalar() or 0.0,
        "total_tokens_today": total_tokens.scalar() or 0,
        "cost_by_model": {row[0]: row[1] for row in cost_by_model.all()}
    }
