from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Agent, User, AgentLevel
import uuid

router = APIRouter()

@router.post("/")
async def create_agent(
    name: str,
    provider: str,
    model: str,
    capabilities: List[str],
    level: AgentLevel = AgentLevel.JUNIOR,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = Agent(
        id=str(uuid.uuid4()),
        name=name,
        provider=provider,
        model=model,
        capabilities=capabilities,
        level=level,
        org_id=current_user.org_id,
        team_id=current_user.team_id
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent

@router.get("/")
async def list_agents(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Agent).where(Agent.org_id == current_user.org_id)
    if status:
        query = query.where(Agent.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == current_user.org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
