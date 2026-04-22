"""Advanced Search Service for FleetOps

Features:
- Full-text search across tasks, agents, events, conversations
- Filtering by multiple criteria
- Faceted search (by status, priority, channel, date)
- Saved searches
- Search suggestions
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.models.models import (
    Task, Agent, Event, Approval, User, Organization,
    TaskStatus, RiskLevel
)

class SearchFilter:
    """Search filter configuration"""
    def __init__(self):
        self.status: Optional[List[str]] = None
        self.priority: Optional[List[str]] = None
        self.agent_id: Optional[str] = None
        self.org_id: Optional[str] = None
        self.team_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.date_from: Optional[datetime] = None
        self.date_to: Optional[datetime] = None
        self.channel: Optional[str] = None
        self.risk_level: Optional[List[str]] = None
        self.tags: Optional[List[str]] = None
        self.search_text: Optional[str] = None

class SearchService:
    """Advanced search across FleetOps data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.saved_searches: Dict[str, Dict] = {}
    
    async def search_tasks(self, filters: SearchFilter, 
                           page: int = 1, page_size: int = 20) -> Dict:
        """Search tasks with filters"""
        query = select(Task)
        
        # Apply filters
        conditions = []
        
        if filters.search_text:
            conditions.append(
                or_(
                    Task.title.ilike(f"%{filters.search_text}%"),
                    Task.description.ilike(f"%{filters.search_text}%")
                )
            )
        
        if filters.status:
            conditions.append(Task.status.in_([TaskStatus(s) for s in filters.status]))
        
        if filters.priority:
            conditions.append(Task.risk_level.in_([RiskLevel(p) for p in filters.priority]))
        
        if filters.agent_id:
            conditions.append(Task.agent_id == filters.agent_id)
        
        if filters.org_id:
            conditions.append(Task.org_id == filters.org_id)
        
        if filters.date_from:
            conditions.append(Task.created_at >= filters.date_from)
        
        if filters.date_to:
            conditions.append(Task.created_at <= filters.date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(Task.id)).select_from(Task)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Task.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        # Get facets
        facets = await self._get_task_facets(filters)
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "results": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                    "risk_level": t.risk_level.value if hasattr(t.risk_level, 'value') else str(t.risk_level),
                    "stage": t.stage,
                    "agent_id": t.agent_id,
                    "org_id": t.org_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None
                }
                for t in tasks
            ],
            "facets": facets
        }
    
    async def _get_task_facets(self, base_filters: SearchFilter) -> Dict:
        """Get facet counts for tasks"""
        facets = {}
        
        # Status facet
        status_result = await self.db.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        )
        facets["status"] = [
            {"value": str(s), "count": c} for s, c in status_result.all()
        ]
        
        # Risk level facet
        risk_result = await self.db.execute(
            select(Task.risk_level, func.count(Task.id)).group_by(Task.risk_level)
        )
        facets["risk_level"] = [
            {"value": str(r), "count": c} for r, c in risk_result.all()
        ]
        
        # Date facet (by month)
        date_result = await self.db.execute(
            select(
                func.date_trunc('month', Task.created_at).label('month'),
                func.count(Task.id)
            ).group_by('month').order_by('month')
        )
        facets["month"] = [
            {"value": str(m), "count": c} for m, c in date_result.all()
        ]
        
        return facets
    
    async def search_agents(self, filters: SearchFilter,
                           page: int = 1, page_size: int = 20) -> Dict:
        """Search agents with filters"""
        query = select(Agent)
        
        conditions = []
        
        if filters.search_text:
            conditions.append(
                or_(
                    Agent.name.ilike(f"%{filters.search_text}%"),
                    Agent.provider.ilike(f"%{filters.search_text}%"),
                    Agent.model.ilike(f"%{filters.search_text}%")
                )
            )
        
        if filters.org_id:
            conditions.append(Agent.org_id == filters.org_id)
        
        if filters.team_id:
            conditions.append(Agent.team_id == filters.team_id)
        
        if filters.status:
            conditions.append(Agent.status.in_(filters.status))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(Agent.id)).select_from(Agent)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Agent.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        agents = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "results": [
                {
                    "id": a.id,
                    "name": a.name,
                    "provider": a.provider,
                    "model": a.model,
                    "level": a.level.value if hasattr(a.level, 'value') else str(a.level),
                    "status": a.status,
                    "org_id": a.org_id,
                    "team_id": a.team_id,
                    "capabilities": a.capabilities,
                    "cost_to_date": a.cost_to_date,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in agents
            ]
        }
    
    async def search_events(self, filters: SearchFilter,
                           page: int = 1, page_size: int = 50) -> Dict:
        """Search events with filters"""
        query = select(Event)
        
        conditions = []
        
        if filters.search_text:
            conditions.append(Event.data.cast(str).ilike(f"%{filters.search_text}%"))
        
        if filters.agent_id:
            conditions.append(Event.agent_id == filters.agent_id)
        
        if filters.date_from:
            conditions.append(Event.timestamp >= filters.date_from)
        
        if filters.date_to:
            conditions.append(Event.timestamp <= filters.date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Event.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        return {
            "page": page,
            "page_size": page_size,
            "results": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "task_id": e.task_id,
                    "agent_id": e.agent_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "data": e.data
                }
                for e in events
            ]
        }
    
    def save_search(self, user_id: str, name: str, 
                    entity_type: str, filters: Dict) -> Dict:
        """Save a search for later use"""
        search_id = f"search_{user_id}_{datetime.utcnow().timestamp()}"
        
        self.saved_searches[search_id] = {
            "id": search_id,
            "user_id": user_id,
            "name": name,
            "entity_type": entity_type,
            "filters": filters,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {"search_id": search_id, "status": "saved"}
    
    def get_saved_searches(self, user_id: str) -> List[Dict]:
        """Get saved searches for user"""
        return [
            search for search in self.saved_searches.values()
            if search["user_id"] == user_id
        ]
    
    def get_search_suggestions(self, entity_type: str, 
                              partial: str) -> List[str]:
        """Get search suggestions"""
        suggestions = []
        
        if entity_type == "tasks":
            suggestions = [
                "status:completed",
                "status:pending risk_level:high",
                "agent_id:agent_123",
                "created_after:2026-01-01",
                "stage:execution"
            ]
        elif entity_type == "agents":
            suggestions = [
                "provider:anthropic",
                "status:active",
                "level:senior",
                "capabilities:customer_service"
            ]
        elif entity_type == "events":
            suggestions = [
                "event_type:approval",
                "agent_id:agent_123",
                "today",
                "last_7_days"
            ]
        
        return [s for s in suggestions if partial.lower() in s.lower()]
