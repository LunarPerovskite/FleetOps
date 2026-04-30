from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Team, User
import uuid

router = APIRouter()

class CreateTeamRequest(BaseModel):
    name: str
    org_id: Optional[str] = None

@router.post("/")
async def create_team(
    data: CreateTeamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = Team(id=str(uuid.uuid4()), name=data.name, org_id=data.org_id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team

@router.get("/")
async def list_teams(
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if org_id:
        result = await db.execute(select(Team).where(Team.org_id == org_id))
    else:
        result = await db.execute(select(Team))
    return result.scalars().all()
