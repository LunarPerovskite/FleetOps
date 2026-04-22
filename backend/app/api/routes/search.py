"""Search API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.search_service import SearchService, SearchFilter
from app.models.models import User

router = APIRouter()

@router.post("/tasks")
async def search_tasks(
    filters: dict,
    page: Optional[int] = 1,
    page_size: Optional[int] = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search tasks with filters"""
    search_service = SearchService(db)
    
    filter_obj = SearchFilter()
    filter_obj.search_text = filters.get("search_text")
    filter_obj.status = filters.get("status")
    filter_obj.priority = filters.get("priority")
    filter_obj.agent_id = filters.get("agent_id")
    filter_obj.org_id = current_user.org_id
    filter_obj.date_from = filters.get("date_from")
    filter_obj.date_to = filters.get("date_to")
    
    result = await search_service.search_tasks(filter_obj, page, page_size)
    return result

@router.post("/agents")
async def search_agents(
    filters: dict,
    page: Optional[int] = 1,
    page_size: Optional[int] = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search agents with filters"""
    search_service = SearchService(db)
    
    filter_obj = SearchFilter()
    filter_obj.search_text = filters.get("search_text")
    filter_obj.org_id = current_user.org_id
    filter_obj.team_id = filters.get("team_id")
    filter_obj.status = filters.get("status")
    
    result = await search_service.search_agents(filter_obj, page, page_size)
    return result

@router.post("/events")
async def search_events(
    filters: dict,
    page: Optional[int] = 1,
    page_size: Optional[int] = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search events with filters"""
    search_service = SearchService(db)
    
    filter_obj = SearchFilter()
    filter_obj.search_text = filters.get("search_text")
    filter_obj.agent_id = filters.get("agent_id")
    filter_obj.date_from = filters.get("date_from")
    filter_obj.date_to = filters.get("date_to")
    
    result = await search_service.search_events(filter_obj, page, page_size)
    return result

@router.get("/suggestions")
async def get_search_suggestions(
    entity_type: str,
    partial: str,
    current_user: User = Depends(get_current_user)
):
    """Get search suggestions"""
    search_service = SearchService(None)
    suggestions = search_service.get_search_suggestions(entity_type, partial)
    return {"suggestions": suggestions}
