"""Dashboard Builder API for FleetOps

Save and manage custom dashboard layouts
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User

router = APIRouter(prefix="/dashboard-builder", tags=["Dashboard Builder"])

# In-memory storage (use database in production)
dashboards: Dict[str, List[Dict[str, Any]]] = {}

WIDGET_TYPES = {
    "stats": {
        "name": "Stats Overview",
        "description": "Key metrics cards",
        "icon": "BarChart3",
        "default_data": {"total_tasks": 0, "active_agents": 0, "pending_approvals": 0, "cost_today": 0}
    },
    "tasks": {
        "name": "Tasks List",
        "description": "Recent tasks with status",
        "icon": "CheckSquare",
        "default_data": []
    },
    "approvals": {
        "name": "Pending Approvals",
        "description": "Items awaiting approval",
        "icon": "Shield",
        "default_data": []
    },
    "agents": {
        "name": "Agent Status",
        "description": "Active agents overview",
        "icon": "Bot",
        "default_data": []
    },
    "chart": {
        "name": "Analytics Chart",
        "description": "Performance visualization",
        "icon": "LineChart",
        "default_data": {"labels": [], "values": []}
    },
    "activity": {
        "name": "Activity Feed",
        "description": "Recent activity log",
        "icon": "Activity",
        "default_data": []
    }
}

@router.get("/widgets")
def get_widget_types(
    current_user: User = Depends(get_current_user)
):
    """Get available widget types"""
    return {"widgets": WIDGET_TYPES}

@router.get("/dashboards")
def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List saved dashboards"""
    org_id = current_user.org_id
    user_dashboards = dashboards.get(org_id, [])
    return {"dashboards": user_dashboards}

@router.post("/dashboards")
def create_dashboard(
    name: str,
    widgets: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom dashboard"""
    org_id = current_user.org_id
    
    if org_id not in dashboards:
        dashboards[org_id] = []
    
    dashboard = {
        "id": f"dashboard_{len(dashboards[org_id]) + 1}",
        "name": name,
        "widgets": widgets,
        "created_by": current_user.id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    dashboards[org_id].append(dashboard)
    return dashboard

@router.get("/dashboards/{dashboard_id}")
def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific dashboard"""
    org_id = current_user.org_id
    user_dashboards = dashboards.get(org_id, [])
    
    for dashboard in user_dashboards:
        if dashboard["id"] == dashboard_id:
            return dashboard
    
    raise HTTPException(status_code=404, detail="Dashboard not found")

@router.put("/dashboards/{dashboard_id}")
def update_dashboard(
    dashboard_id: str,
    name: Optional[str] = None,
    widgets: Optional[List[Dict[str, Any]]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update dashboard layout"""
    org_id = current_user.org_id
    user_dashboards = dashboards.get(org_id, [])
    
    for dashboard in user_dashboards:
        if dashboard["id"] == dashboard_id:
            if name:
                dashboard["name"] = name
            if widgets:
                dashboard["widgets"] = widgets
            dashboard["updated_at"] = datetime.utcnow().isoformat()
            return dashboard
    
    raise HTTPException(status_code=404, detail="Dashboard not found")

@router.delete("/dashboards/{dashboard_id}")
def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dashboard"""
    org_id = current_user.org_id
    user_dashboards = dashboards.get(org_id, [])
    
    for i, dashboard in enumerate(user_dashboards):
        if dashboard["id"] == dashboard_id:
            user_dashboards.pop(i)
            return {"message": "Dashboard deleted"}
    
    raise HTTPException(status_code=404, detail="Dashboard not found")
