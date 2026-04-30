"""Search API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.services.search_service import SearchService, SearchFilter
from app.models.models import User

router = APIRouter()

@router.post("/")
async def global_search(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Global search across all entities"""
    query = body.get("query", "")
    filters = body.get("filters", {})
    
    if not query or len(query) < 2:
        return {"results": [], "total": 0}
    
    search_service = SearchService(db)
    results = []
    
    # Search agents
    try:
        agent_filter = SearchFilter()
        agent_filter.search_text = query
        agent_filter.org_id = current_user.org_id
        if filters.get("types"):
            agent_filter.status = filters.get("types", [])
        
        agent_results = await search_service.search_agents(agent_filter, 1, 10)
        if agent_results and agent_results.get("items"):
            for agent in agent_results["items"]:
                results.append({
                    "id": str(agent.get("id", "")),
                    "type": "agent",
                    "title": agent.get("name", "Unnamed Agent"),
                    "description": agent.get("description") or f"{agent.get('provider', 'unknown')} agent",
                    "url": f"/agents/{agent.get('id', '')}",
                    "metadata": {
                        "provider": agent.get("provider"),
                        "status": agent.get("status"),
                        "model": agent.get("model"),
                    },
                    "score": 0.9,
                })
    except Exception:
        pass
    
    # Search tasks
    try:
        task_filter = SearchFilter()
        task_filter.search_text = query
        task_filter.org_id = current_user.org_id
        
        task_results = await search_service.search_tasks(task_filter, 1, 10)
        if task_results and task_results.get("items"):
            for task in task_results["items"]:
                results.append({
                    "id": str(task.get("id", "")),
                    "type": "task",
                    "title": task.get("title", "Untitled Task"),
                    "description": task.get("description") or f"Status: {task.get('status', 'unknown')}",
                    "url": f"/tasks/{task.get('id', '')}",
                    "metadata": {
                        "status": task.get("status"),
                        "priority": task.get("priority"),
                        "agent_id": task.get("agent_id"),
                    },
                    "score": 0.85,
                })
    except Exception:
        pass
    
    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "results": results[:20],
        "total": len(results),
        "query": query,
    }

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
