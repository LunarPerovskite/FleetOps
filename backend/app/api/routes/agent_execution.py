"""Agent Execution API Routes for FleetOps

Endpoints for executing tasks through AI agents:
- OpenClaw, Hermes, or any personal agent
- Handles submission, polling, approval, and cancellation
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Optional

from app.core.auth import get_current_user
from app.models.models import User
from app.services.agent_execution_service import agent_execution_service

router = APIRouter(prefix="/agent-execute", tags=["Agent Execution"])

@router.post("/{task_id}")
async def execute_with_agent(
    task_id: str,
    agent_type: str = Query("openclaw", description="Agent type: openclaw, hermes, ollama, custom"),
    auto_approve_low_risk: bool = Query(False, description="Auto-approve low-risk steps"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """Execute a FleetOps task using an AI agent

    This submits the task to the agent and starts execution
    in the background. The task status will be updated as
    the agent progresses.

    Returns immediately with execution tracking info.
    """
    try:
        result = await agent_execution_service.execute_task(
            task_id=task_id,
            agent_type=agent_type,
            auto_approve_low_risk=auto_approve_low_risk
        )

        if result["status"] == "started":
            return {
                "status": "success",
                "message": f"Agent {agent_type} started working on task {task_id}",
                "task_id": task_id,
                "execution_id": result["execution_id"],
                "agent_type": agent_type,
                "check_status_at": f"/api/v1/agent-execute/status/{task_id}"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Execution failed"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_execution_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get current execution status for a task"""
    try:
        status = await agent_execution_service.get_execution_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve/{task_id}")
async def submit_human_approval(
    task_id: str,
    approval_id: str,
    decision: str,  # approve, reject, modify
    comments: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Submit human approval for an agent step

    Called when user approves/rejects agent output in FleetOps UI.
    Forwards the decision to the agent so it can continue.
    """
    try:
        result = await agent_execution_service.handle_human_approval(
            task_id=task_id,
            approval_id=approval_id,
            decision=decision,
            comments=comments
        )

        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"Approval decision '{decision}' sent to agent",
                "task_id": task_id,
                "decision": decision
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{task_id}")
async def cancel_execution(
    task_id: str,
    reason: Optional[str] = "User cancelled",
    current_user: User = Depends(get_current_user)
):
    """Cancel a running agent execution"""
    try:
        result = await agent_execution_service.cancel_execution(task_id, reason)

        if result["status"] == "success":
            return {
                "status": "success",
                "message": "Execution cancelled",
                "task_id": task_id
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# AGENT CONFIGURATION CHECK
# ═══════════════════════════════════════

def check_agent_configured(agent_type: str) -> bool:
    """Check if agent is configured in environment"""
    adapter_info = ALL_ADAPTERS.get(agent_type, {})
    url_env = adapter_info.get("url_env", "")
    if url_env:
        return bool(getattr(settings, url_env, None))
    return False


# ═══════════════════════════════════════
# AGENT LISTING
# ═══════════════════════════════════════

@router.get("/agents")
async def list_supported_agents(
    current_user: User = Depends(get_current_user)
):
    """List all supported agent types and their capabilities"""
    
    agents = {}
    for agent_id, info in ALL_ADAPTERS.items():
        agents[agent_id] = {
            "id": agent_id,
            "name": info["name"],
            "category": info["category"],
            "description": info["description"],
            "capabilities": info.get("capabilities", []),
            "supports_governance": info.get("supports_governance", True),
            "supports_remote": True,
            "config_required": [info.get("url_env", "")] if info.get("url_env") else [],
            "status": "available" if check_agent_configured(agent_id) else "not_configured"
        }
    
    return {
        "agents": agents,
        "categories": ADAPTER_CATEGORIES,
        "total_count": len(agents)
    }
