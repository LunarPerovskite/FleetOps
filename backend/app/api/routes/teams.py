from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import Team, User
import uuid

router = APIRouter()

@router.post("/")
async def create_team(name: str, org_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = Team(id=str(uuid.uuid4()), name=name, org_id=org_id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team

@router.get("/")
async def list_teams(org_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Team).where(Team.org_id == org_id))
    return result.scalars().all()
