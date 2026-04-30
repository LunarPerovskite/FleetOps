from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.websocket import manager
from app.core.database import get_db
from app.models.models import Agent, User, HumanRole

router = APIRouter()

@router.websocket("/ws")
async def generic_websocket(websocket: WebSocket):
    """Generic WebSocket for frontend connections (no auth required)"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
            else:
                await websocket.send_json({"type": "ack", "received": data})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str, db: AsyncSession = Depends(get_db)):
    """WebSocket for agents to connect from any machine"""
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        await websocket.close(code=4001, reason="Agent not found")
        return
    
    await manager.connect_agent(agent_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types from agents
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
            
            elif data.get("type") == "task_event":
                # Agent reporting task progress
                await manager.notify_task_update(
                    agent_id=agent_id,
                    task_id=data.get("task_id"),
                    status=data.get("status"),
                    stage=data.get("stage")
                )
            
            elif data.get("type") == "request_approval":
                # Agent requesting human approval
                sla = data.get("sla_deadline")
                if isinstance(sla, str):
                    # Parse ISO 8601 string to datetime
                    sla = datetime.fromisoformat(sla.replace("Z", "+00:00"))
                elif not isinstance(sla, datetime):
                    sla = None  # Default if invalid type
                await manager.notify_approval_needed(
                    task_id=data.get("task_id"),
                    stage=data.get("stage"),
                    required_role=data.get("required_role", "operator"),
                    sla_deadline=sla,
                    org_id=agent.org_id
                )
            
            elif data.get("type") == "llm_usage":
                # Agent reporting LLM usage
                pass  # Handled via HTTP API
            
    except WebSocketDisconnect:
        manager.disconnect_agent(agent_id)

@router.websocket("/ws/human/{user_id}")
async def human_websocket(websocket: WebSocket, user_id: str, db: AsyncSession = Depends(get_db)):
    """WebSocket for humans to connect from any machine"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        await websocket.close(code=4001, reason="User not found")
        return
    
    await manager.connect_human(user_id, user.org_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
            
            elif data.get("type") == "approval_decision":
                # Human sending approval decision
                # Forward to the relevant agent
                task_id = data.get("task_id")
                decision = data.get("decision")
                
                # Find the task's agent and notify
                from app.models.models import Task
                result = await db.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if task and task.agent_id:
                    await manager.send_to_agent(task.agent_id, {
                        "type": "approval_response",
                        "task_id": task_id,
                        "decision": decision,
                        "human_id": user_id,
                        "comments": data.get("comments")
                    })
            
            elif data.get("type") == "delegate_to_subagent":
                # Human delegating a task to a sub-agent
                parent_agent_id = data.get("parent_agent_id")
                sub_agent_id = data.get("sub_agent_id")
                task_id = data.get("task_id")
                
                # Notify parent agent
                await manager.send_to_agent(parent_agent_id, {
                    "type": "subagent_assigned",
                    "sub_agent_id": sub_agent_id,
                    "task_id": task_id
                })
                
                # Notify sub-agent
                await manager.send_to_agent(sub_agent_id, {
                    "type": "task_assigned",
                    "task_id": task_id,
                    "parent_agent_id": parent_agent_id
                })
    
    except WebSocketDisconnect:
        manager.disconnect_human(user_id, user.org_id)
