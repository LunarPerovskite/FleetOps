"""Shared Agent API Routes

Allows agents to be shared across teams within an organization.
Each team gets its own budget allocation and usage tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, Agent, Team, AgentTeamAssignment

router = APIRouter()

@router.get("/teams/{team_id}/shared-agents")
async def get_team_shared_agents(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shared agents for a team"""
    # Verify team exists and user has access
    team = await db.get(Team, team_id)
    if not team or team.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Team not found")
    
    stmt = select(AgentTeamAssignment).where(
        and_(
            AgentTeamAssignment.team_id == team_id,
            AgentTeamAssignment.is_active == True
        )
    )
    result = await db.execute(stmt)
    assignments = result.scalars().all()
    
    return {
        "team_id": team_id,
        "shared_agents": [
            {
                "id": str(a.id),
                "agent_id": str(a.agent_id),
                "agent_name": a.agent.name if a.agent else "Unknown",
                "agent_provider": a.agent.provider if a.agent else "unknown",
                "budget_allocation": a.budget_allocation,
                "usage_limit": a.usage_limit,
                "current_usage": a.current_usage,
                "permissions": a.permissions,
                "assigned_by": a.assigned_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in assignments
        ],
        "total": len(assignments)
    }

@router.post("/teams/{team_id}/shared-agents")
async def share_agent_to_team(
    team_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Share an agent with a team"""
    agent_id = data.get("agent_id")
    
    # Verify agent exists and belongs to same org
    agent = await db.get(Agent, agent_id)
    if not agent or agent.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Verify team exists and belongs to same org
    team = await db.get(Team, team_id)
    if not team or team.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if agent is already shared with this team
    existing = await db.execute(
        select(AgentTeamAssignment).where(
            and_(
                AgentTeamAssignment.agent_id == agent_id,
                AgentTeamAssignment.team_id == team_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent already shared with this team")
    
    # Create assignment
    assignment = AgentTeamAssignment(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        team_id=team_id,
        org_id=current_user.org_id,
        assigned_by=str(current_user.id),
        budget_allocation=data.get("budget_allocation", 0.0),
        usage_limit=data.get("usage_limit"),
        permissions=data.get("permissions", ["read", "execute"]),
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(assignment)
    await db.commit()
    
    # Mark agent as shared
    agent.is_shared = True
    await db.commit()
    
    return {
        "id": str(assignment.id),
        "agent_id": str(agent_id),
        "team_id": str(team_id),
        "message": f"Agent '{agent.name}' shared with team '{team.name}'"
    }

@router.put("/teams/{team_id}/shared-agents/{assignment_id}")
async def update_shared_agent(
    team_id: str,
    assignment_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update shared agent permissions/budget"""
    assignment = await db.get(AgentTeamAssignment, assignment_id)
    if not assignment or assignment.team_id != team_id:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    if "budget_allocation" in data:
        assignment.budget_allocation = data["budget_allocation"]
    if "usage_limit" in data:
        assignment.usage_limit = data["usage_limit"]
    if "permissions" in data:
        assignment.permissions = data["permissions"]
    if "is_active" in data:
        assignment.is_active = data["is_active"]
    
    await db.commit()
    
    return {
        "id": str(assignment.id),
        "budget_allocation": assignment.budget_allocation,
        "usage_limit": assignment.usage_limit,
        "permissions": assignment.permissions,
        "is_active": assignment.is_active
    }

@router.delete("/teams/{team_id}/shared-agents/{assignment_id}")
async def remove_shared_agent(
    team_id: str,
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove shared agent from team"""
    assignment = await db.get(AgentTeamAssignment, assignment_id)
    if not assignment or assignment.team_id != team_id:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.delete(assignment)
    await db.commit()
    
    return {"message": "Shared agent removed from team"}

@router.get("/agents/{agent_id}/shared-teams")
async def get_agent_shared_teams(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all teams an agent is shared with"""
    agent = await db.get(Agent, agent_id)
    if not agent or agent.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    stmt = select(AgentTeamAssignment).where(
        and_(
            AgentTeamAssignment.agent_id == agent_id,
            AgentTeamAssignment.is_active == True
        )
    )
    result = await db.execute(stmt)
    assignments = result.scalars().all()
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "is_shared": agent.is_shared,
        "shared_with_teams": [
            {
                "team_id": str(a.team_id),
                "team_name": a.team.name if a.team else "Unknown",
                "budget_allocation": a.budget_allocation,
                "usage_limit": a.usage_limit,
                "current_usage": a.current_usage,
                "permissions": a.permissions,
            }
            for a in assignments
        ],
        "total_shared": len(assignments)
    }

@router.get("/orgs/shared-agents")
async def get_org_shared_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shared agents in organization"""
    stmt = select(Agent).where(
        and_(
            Agent.org_id == current_user.org_id,
            Agent.is_shared == True
        )
    )
    result = await db.execute(stmt)
    agents = result.scalars().all()
    
    return {
        "organization_id": str(current_user.org_id),
        "shared_agents": [
            {
                "id": str(a.id),
                "name": a.name,
                "provider": a.provider,
                "model": a.model,
                "home_team_id": str(a.team_id) if a.team_id else None,
                "home_team_name": a.team.name if a.team else "None",
                "shared_teams_count": len(a.shared_assignments) if a.shared_assignments else 0,
                "cost_to_date": a.cost_to_date,
                "status": a.status,
            }
            for a in agents
        ],
        "total": len(agents)
    }
