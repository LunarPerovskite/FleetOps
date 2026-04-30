from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.models import Organization
import uuid

router = APIRouter()

class CreateOrgRequest(BaseModel):
    name: str

@router.post("/")
async def create_organization(data: CreateOrgRequest, db: AsyncSession = Depends(get_db)):
    org = Organization(id=str(uuid.uuid4()), name=data.name)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization))
    return result.scalars().all()
