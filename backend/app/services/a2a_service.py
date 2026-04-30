"""Google A2A Task Routing Service — FleetOps Governance Hub

FleetOps sits between sender agents and receiver agents.
No agent talks directly to another — every task goes through FleetOps
which enforces governance, logging, and discovery.

Design (per Google A2A spec):
  1. Agent publishes Agent Card at /.well-known/agent.json
  2. FleetOps discovers agents by reading their cards
  3. Agent sends task to FleetOps (via /tasks/send)
  4. FleetOps checks governance rules
  5. FleetOps routes task to the target agent
  6. FleetOps streams back SSE updates from the agent
  7. FleetOps logs every interaction to the Event table for audit
"""

import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime
import uuid
import httpx

from app.core.a2a import (
    Task, TaskState, TaskSendParams, Message,
    AgentCard, AgentSkill, AgentCapabilities,
    TaskStatusUpdateEvent, TaskArtifactUpdateEvent,
    A2AError
)
from app.core.logging_config import get_logger

logger = get_logger("fleetops.a2a")


class A2ARegistry:
    """Registry of known remote agents and their Agent Cards.

    In production this should be backed by Redis so it survives restarts
    and works across multiple FleetOps worker processes.
    """

    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}       # agent_id -> AgentCard
        self._agent_urls: Dict[str, str] = {}          # agent_id -> task sending URL
        self._last_seen: Dict[str, datetime] = {}

    def register(self, agent_id: str, card: AgentCard, url: str) -> None:
        """Register a remote agent after reading its Agent Card."""
        self._agents[agent_id] = card
        self._agent_urls[agent_id] = url
        self._last_seen[agent_id] = datetime.utcnow()
        logger.info(f"Registered agent {agent_id} ({card.name}) with {len(card.skills)} skills")

    def get(self, agent_id: str) -> Optional[AgentCard]:
        return self._agents.get(agent_id)

    def get_url(self, agent_id: str) -> Optional[str]:
        return self._agent_urls.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "agent_id": aid,
                "name": card.name,
                "framework": card.name,
                "status": "online",
                "last_seen": self._last_seen.get(aid),
                "skills": [{"id": s.id, "name": s.name, "tags": s.tags} for s in card.skills]
            }
            for aid, card in self._agents.items()
        ]

    def discover_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        results = []
        for aid, card in self._agents.items():
            for s in card.skills:
                if skill in s.tags or skill.lower() in s.name.lower():
                    results.append({
                        "agent_id": aid,
                        "name": card.name,
                        "skill_id": s.id,
                        "skill_name": s.name
                    })
        return results

    def cleanup_stale(self, max_age_seconds: int = 300) -> int:
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(seconds=max_age_seconds)
        stale = [aid for aid, ts in self._last_seen.items() if ts < cutoff]
        for aid in stale:
            self._agents.pop(aid, None)
            self._agent_urls.pop(aid, None)
            self._last_seen.pop(aid, None)
        if stale:
            logger.info(f"Cleaned up {len(stale)} stale A2A agents")
        return len(stale)


class A2AService:
    """FleetOps A2A governance hub — routes tasks between agents with full audit."""

    def __init__(self):
        self.registry = A2ARegistry()
        self._tasks: Dict[str, Task] = {}       # task_id -> Task
        self._conversations: Dict[str, List[Task]] = {}  # session_id -> [Task]
        self._pending_approvals: Dict[str, str] = {}  # task_id -> approval_id

    # ── Agent Discovery ──

    async def read_agent_card(self, url: str) -> Optional[AgentCard]:
        """Fetch and parse a remote agent's Agent Card."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{url.rstrip('/')}/.well-known/agent.json"
                )
                response.raise_for_status()
                data = response.json()
                return AgentCard(**data)
        except Exception as e:
            logger.warning(f"Failed to read agent card at {url}: {e}")
            return None

    async def register_agent(self, agent_id: str, url: str) -> bool:
        """Discover a remote agent by reading its Agent Card and register it."""
        card = await self.read_agent_card(url)
        if not card:
            return False
        self.registry.register(agent_id, card, url)
        return True

    # ── Task Lifecycle ──

    async def send_task(self, params: TaskSendParams, org_id: str) -> Task:
        """Handle /tasks/send — the main entry point for A2A tasks.

        FleetOps governance flow:
        1. Create Task
        2. Identify target agent (from metadata or discovery)
        3. Check if approval needed
        4a. If approved → forward to target agent
        4b. If pending → return task with status=input-required
        5. Log everything to Event table
        """
        # 1. Create the Task
        task = Task.new(session_id=params.sessionId, metadata=params.metadata)
        task.org_id = org_id
        task.history.append(params.message)

        # Extract routing info from metadata
        to_agent_id = params.metadata.get("to_agent_id", "")
        task.to_agent_id = to_agent_id

        self._tasks[task.id] = task
        if task.sessionId not in self._conversations:
            self._conversations[task.sessionId] = []
        self._conversations[task.sessionId].append(task)

        # 2. Log event to FleetOps audit
        await self._log_task_event(task, "task_created", org_id)

        # 3. If no target agent specified, we're done (task is created, waiting for routing)
        if not to_agent_id:
            return task

        # 4. Check governance
        governance_result = await self._check_governance(task)
        if governance_result["blocked"]:
            task.status = TaskState.INPUT_REQUIRED
            task.governance_status = "pending_approval"
            task.metadata["governance"] = governance_result
            await self._log_task_event(task, "governance_blocked", org_id)
            return task

        # 5. Forward to target agent
        await self._route_to_agent(task, to_agent_id)
        return task

    async def get_task(self, task_id: str, org_id: str) -> Optional[Task]:
        """Handle /tasks/get — return task status."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        if task.org_id != org_id:
            return None  # Cross-org isolation
        return task

    async def cancel_task(self, task_id: str, org_id: str) -> bool:
        """Handle /tasks/cancel — cancel a running task."""
        task = self._tasks.get(task_id)
        if not task or task.org_id != org_id:
            return False
        if task.status in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED):
            return False  # Can't cancel terminal tasks

        task.status = TaskState.CANCELED
        await self._log_task_event(task, "task_canceled", org_id)

        # Also send cancel to the remote agent if it's currently working
        if task.to_agent_id:
            await self._send_cancel_to_agent(task, task.to_agent_id)
        return True

    async def update_task_status(self, task_id: str, status: str,
                                 message: Optional[Message] = None,
                                 artifacts: Optional[List[Any]] = None) -> None:
        """Called when a remote agent updates task status (via push notification or polling)."""
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = status
        if message:
            task.history.append(message)
        if artifacts:
            task.artifacts.extend(artifacts)

        # Persist to FleetOps audit
        await self._log_task_event(task, f"task_status_{status}", task.org_id)

    # ── Streaming (SSE) ──

    async def stream_task(self, params: TaskSendParams, org_id: str) -> AsyncGenerator[str, None]:
        """Handle /tasks/sendSubscribe — stream SSE updates as the task progresses.

        Yields Server-Sent Event lines for status updates and artifacts.
        """
        task = await self.send_task(params, org_id)
        if not task:
            yield TaskStatusUpdateEvent(
                id="", status=TaskState.FAILED, final=True,
                message=Message(role="agent", parts=[{"type": "text", "text": "Failed to create task"}])
            ).to_sse()
            return

        # Yield initial status
        yield TaskStatusUpdateEvent(id=task.id, status=task.status).to_sse()

        if task.status == TaskState.INPUT_REQUIRED:
            # Waiting for governance approval
            yield TaskStatusUpdateEvent(
                id=task.id, status=TaskState.INPUT_REQUIRED, final=False,
                message=Message(role="agent", parts=[{
                    "type": "text",
                    "text": f"Task {task.id} requires human approval before routing to agent {task.to_agent_id}"
                }])
            ).to_sse()
            return

        # Stream from the remote agent (this would poll or receive pushes in production)
        # For now, yield a single completion
        yield TaskStatusUpdateEvent(id=task.id, status=task.status, final=True).to_sse()

    # ── Governance ──

    async def _check_governance(self, task: Task) -> Dict[str, Any]:
        """Check if this A2A task needs human approval before routing."""
        # Risky operations that need approval
        risky_skills = {"file_delete", "shell_exec", "git_force_push", "database_drop"}
        target_skill = task.metadata.get("skill", "")

        if target_skill in risky_skills:
            # Create approval request
            approval_id = str(uuid.uuid4())
            self._pending_approvals[task.id] = approval_id

            # Broadcast to org for human review
            from app.core.websocket import manager
            await manager.broadcast_to_org(task.org_id, {
                "type": "a2a_approval_needed",
                "approval_id": approval_id,
                "task_id": task.id,
                "from_agent": task.from_agent_id,
                "to_agent": task.to_agent_id,
                "skill": target_skill,
                "description": f"Agent {task.from_agent_id} wants {task.to_agent_id} to execute '{target_skill}'"
            })

            return {
                "blocked": True,
                "reason": f"Skill '{target_skill}' requires human approval",
                "approval_id": approval_id
            }

        return {"blocked": False}

    async def approve_task(self, task_id: str, approval_id: str) -> bool:
        """Human approved an A2A task — route it now."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        stored_approval = self._pending_approvals.get(task_id)
        if stored_approval != approval_id:
            return False

        task.governance_status = "approved"
        del self._pending_approvals[task_id]

        await self._route_to_agent(task, task.to_agent_id)
        await self._log_task_event(task, "task_approved_and_routed", task.org_id)
        return True

    # ── Internal routing ──

    async def _route_to_agent(self, task: Task, agent_id: str) -> bool:
        """Forward a FleetOps-approved task to the target agent's /tasks/send."""
        card = self.registry.get(agent_id)
        url = self.registry.get_url(agent_id)
        if not card or not url:
            logger.error(f"Target agent {agent_id} not registered")
            task.status = TaskState.FAILED
            return False

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{url.rstrip('/')}/tasks/send",
                    json={
                        "id": task.id,
                        "sessionId": task.sessionId,
                        "message": task.history[-1].to_dict() if task.history else {},
                        "metadata": {
                            **task.metadata,
                            "fleetops_routed": True,
                            "fleetops_org_id": task.org_id
                        }
                    }
                )
                response.raise_for_status()
                agent_result = response.json()

                # Copy agent's result back into our task
                task.status = agent_result.get("status", TaskState.WORKING)
                await self._log_task_event(task, "task_routed_and_response", task.org_id)
                return True
        except Exception as e:
            logger.error(f"Failed to route task {task.id} to agent {agent_id}: {e}")
            task.status = TaskState.FAILED
            task.metadata["routing_error"] = str(e)
            return False

    async def _send_cancel_to_agent(self, task: Task, agent_id: str) -> None:
        """Send cancel request to a remote agent."""
        url = self.registry.get_url(agent_id)
        if not url:
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{url.rstrip('/')}/tasks/cancel",
                    json={"id": task.id}
                )
        except Exception:
            pass

    # ── Audit ──

    async def _log_task_event(self, task: Task, event_type: str, org_id: str) -> None:
        """Log every A2A interaction to the FleetOps Event table for audit."""
        try:
            from app.services.service_stubs import event_service
            await event_service.create_event(
                task_id=task.id,
                event_type=f"a2a_{event_type}",
                details={
                    "task_id": task.id,
                    "session_id": task.sessionId,
                    "status": task.status,
                    "to_agent": task.to_agent_id,
                    "from_agent": task.from_agent_id,
                    "org_id": org_id
                },
                agent_id=task.from_agent_id
            )
        except Exception as e:
            logger.warning(f"Failed to log A2A event: {e}")


# Singleton
a2a_service = A2AService()
