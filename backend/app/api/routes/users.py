from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, HumanRole
import uuid

router = APIRouter()

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/")
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.org_id == current_user.org_id))
    return result.scalars().all()
