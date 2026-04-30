"""Google A2A Protocol API Routes — FleetOps Governance Hub

Official A2A endpoints per Google spec:
  GET   /.well-known/agent.json              → FleetOps Agent Card
  POST  /tasks/send                         → Send task (blocking)
  POST  /tasks/sendSubscribe                → Send task (SSE streaming)
  POST  /tasks/get                          → Get task status
  POST  /tasks/cancel                       → Cancel task
  POST  /tasks/approve                      → Approve a pending task (FleetOps extension)
  POST  /agents/register                    → Register a remote A2A agent
  GET   /agents                             → List registered agents
  GET   /agents/discover                    → Find agents by skill tag

FleetOps acts as the A2A hub: agents discover each other through FleetOps
and every task is routed through FleetOps for governance + audit.
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.a2a import (
    Task, TaskState, TaskSendParams, TaskQueryParams,
    AgentCard, AgentSkill, AgentCapabilities,
    A2AError,
)
from app.services.a2a_service import a2a_service
from app.api.routes.auth import get_current_user
from app.models.models import Agent, User

router = APIRouter(tags=["a2a"])




# ─── Task Endpoints ─────────────────────────────────────────────────────────────

@router.post("/tasks/send")
async def tasks_send(
    request: Request,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a task to an agent through FleetOps (blocking).

    Body (per Google A2A spec):
    {
      "id": "task-uuid",
      "sessionId": "session-uuid",
      "message": {"role": "user", "parts": [{"type": "text", "text": "..."}]},
      "metadata": {"to_agent_id": "kilocode-001", "skill": "write_test"},
      "pushNotification": {"url": "...", "token": "..."}
    }

    Example: Claude Code sends a task to KiloCode:
    {
      "message": {"role": "user", "parts": [{"type": "text", "text": "Write a unit test for /api/v1/auth"}]},
      "metadata": {"to_agent_id": "kilocode-001", "skill": "write_test"}
    }
    """
    params = TaskSendParams.from_dict(body)
    try:
        task = await a2a_service.send_task(params, org_id=current_user.org_id)
        return task.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/sendSubscribe")
async def tasks_send_subscribe(
    request: Request,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a task to an agent through FleetOps (SSE streaming).

    Returns Server-Sent Events for task status updates and artifacts.
    """
    params = TaskSendParams.from_dict(body)

    async def event_stream():
        async for event in a2a_service.stream_task(params, org_id=current_user.org_id):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/tasks/get")
async def tasks_get(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current status of a task."""
    task_id = body.get("id")
    if not task_id:
        raise HTTPException(status_code=400, detail="id is required")

    task = await a2a_service.get_task(task_id, org_id=current_user.org_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/tasks/cancel")
async def tasks_cancel(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a running task."""
    task_id = body.get("id")
    if not task_id:
        raise HTTPException(status_code=400, detail="id is required")

    result = await a2a_service.cancel_task(task_id, org_id=current_user.org_id)
    if not result:
        raise HTTPException(status_code=400, detail="Task cannot be canceled")
    return {"status": "canceled", "id": task_id}


# ─── FleetOps Extensions (Governance) ──────────────────────────────────────────

@router.post("/tasks/approve")
async def tasks_approve(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Human approves a pending A2A task. FleetOps extension.

    Body:
    {"task_id": "...", "approval_id": "...", "decision": "approve"}
    """
    task_id = body.get("task_id")
    approval_id = body.get("approval_id")
    decision = body.get("decision", "approve")

    if not task_id or not approval_id:
        raise HTTPException(status_code=400, detail="task_id and approval_id required")

    if decision == "approve":
        result = await a2a_service.approve_task(task_id, approval_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task or approval not found")
        return {"status": "approved", "task_id": task_id}
    else:
        task = await a2a_service.get_task(task_id, current_user.org_id)
        if task:
            task.status = TaskState.CANCELED
        return {"status": "denied", "task_id": task_id}


# ─── Agent Discovery ────────────────────────────────────────────────────────────

@router.post("/agents/register")
async def register_agent(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a remote A2A agent by reading its Agent Card.

    Body:
    {"agent_id": "kilocode-001", "url": "http://kilocode.local:8000"}
    """
    agent_id = body.get("agent_id")
    url = body.get("url")
    if not agent_id or not url:
        raise HTTPException(status_code=400, detail="agent_id and url required")

    result = await a2a_service.register_agent(agent_id, url)
    if not result:
        raise HTTPException(status_code=502, detail="Failed to read agent card")

    return {"status": "registered", "agent_id": agent_id, "url": url}


@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all registered A2A agents."""
    return {"agents": a2a_service.registry.list_agents()}


@router.get("/agents/discover")
async def discover_agents(
    skill: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Discover agents by skill tag."""
    if not skill:
        raise HTTPException(status_code=400, detail="?skill= parameter required")
    matches = a2a_service.registry.discover_by_skill(skill)
    return {"skill": skill, "matches": matches}
