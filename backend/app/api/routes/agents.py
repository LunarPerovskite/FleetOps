from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Agent, User, AgentLevel
import uuid

router = APIRouter()

class CreateAgentRequest(BaseModel):
    name: str
    provider: str
    model: Optional[str] = None
    capabilities: List[str] = []
    level: str = "junior"

@router.post("/")
async def create_agent(
    data: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    level_map = {
        "junior": AgentLevel.JUNIOR,
        "senior": AgentLevel.SENIOR,
        "lead": AgentLevel.LEAD,
        "specialist": AgentLevel.SPECIALIST,
        "monitor": AgentLevel.MONITOR
    }
    agent = Agent(
        id=str(uuid.uuid4()),
        name=data.name,
        provider=data.provider,
        model=data.model or "",
        capabilities=data.capabilities,
        level=level_map.get(data.level, AgentLevel.JUNIOR),
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
    agents = result.scalars().all()
    return {"agents": agents}

@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.org_id == current_user.org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
