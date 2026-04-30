"""Real service implementations replacing placeholder stubs

These are the actual service implementations used by the agent execution service.
They perform real database operations via SQLAlchemy.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from sqlalchemy import select, and_

from app.core.database import _get_async_session_local
from app.models.models import Task, TaskStatus, Event, RiskLevel

# Import ORM Approval with an alias to avoid any naming confusion.
from app.models.models import Approval as ApprovalRecord


# ─── Task Service ────────────────────────────────────────────────────

class TaskService:
    """Real Task Service with async DB operations"""

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a single task by ID"""
        factory = _get_async_session_local()
        async with factory() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            return result.scalar_one_or_none()

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Partial update of a task"""
        factory = _get_async_session_local()
        async with factory() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if not task:
                return False

            for field, value in updates.items():
                if not hasattr(task, field):
                    continue

                # Auto-convert status strings to enum
                if field == "status" and isinstance(value, str):
                    try:
                        value = TaskStatus(value)
                    except ValueError:
                        pass

                # Auto-convert datetime strings
                if field in ("completed_at", "failed_at", "cancelled_at"):
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

                # Stage transitions auto-update status
                if field == "stage":
                    task.stage = value
                    if value == "execution":
                        task.status = TaskStatus.EXECUTING
                    elif value == "review":
                        task.status = TaskStatus.REVIEWING
                    elif value == "delivery":
                        task.status = TaskStatus.COMPLETED
                    elif value == "external_action":
                        task.status = TaskStatus.APPROVAL_PENDING
                    continue

                setattr(task, field, value)

            setattr(task, "updated_at", datetime.utcnow())
            await db.commit()
            await db.refresh(task)
            return True

    async def list_tasks(
        self, org_id: str, status: Optional[str] = None, limit: int = 50
    ) -> List[Task]:
        """List tasks for an org"""
        factory = _get_async_session_local()
        async with factory() as db:
            query = (
                select(Task).where(Task.org_id == org_id)
                .order_by(Task.created_at.desc())
            )
            if status:
                query = query.where(Task.status == status)
            result = await db.execute(query.limit(limit))
            return list(result.scalars().all())

    async def create_task(
        self,
        title: str,
        description: str = "",
        agent_id: Optional[str] = None,
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> Task:
        """Create a new task"""
        factory = _get_async_session_local()
        async with factory() as db:
            task = Task(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                agent_id=agent_id,
                org_id=org_id,
                created_by=created_by,
                risk_level=risk_level,
                status=TaskStatus.CREATED,
                stage="initiation",
                created_at=datetime.utcnow(),
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            return task


# ─── Approval Service ────────────────────────────────────────────────

class ApprovalService:
    """Real Approval Service"""

    async def create_approval(
        self,
        task_id: str,
        stage: str,
        approver_role: str = "operator",
        description: str = "",
        metadata: Optional[Dict] = None,
        created_by: Optional[str] = None,
    ) -> ApprovalRecord:
        """Create a new approval request"""
        factory = _get_async_session_local()
        async with factory() as db:
            sla_deadline = datetime.utcnow() + timedelta(hours=1)
            # Store metadata in comments prefix if we need to keep it;
            # the ORM Approval has no metadata column.
            comments = description
            if metadata:
                import json

                comments = f"[METADATA] {json.dumps(metadata, default=str)}\n---\n{description}"

            approval = ApprovalRecord(
                id=str(uuid.uuid4()),
                task_id=task_id,
                stage=stage,
                comments=comments,
                sla_deadline=sla_deadline,
                created_at=datetime.utcnow(),
            )
            db.add(approval)
            await db.commit()
            await db.refresh(approval)
            return approval

    async def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        """Get an approval by ID"""
        factory = _get_async_session_local()
        async with factory() as db:
            result = await db.execute(
                select(ApprovalRecord).where(ApprovalRecord.id == approval_id)
            )
            return result.scalar_one_or_none()

    async def update_approval(
        self, approval_id: str, decision: str, comments: Optional[str] = None
    ) -> bool:
        """Update approval with a decision"""
        factory = _get_async_session_local()
        async with factory() as db:
            result = await db.execute(
                select(ApprovalRecord).where(ApprovalRecord.id == approval_id)
            )
            approval = result.scalar_one_or_none()
            if not approval:
                return False

            approval.decision = decision
            if comments:
                existing = approval.comments or ""
                approval.comments = (
                    f"{existing}\n---\nDecision: {decision}\nComments: {comments}".strip()
                )
            setattr(approval, "resolved_at", datetime.utcnow())
            await db.commit()
            await db.refresh(approval)
            return True

    async def list_pending(
        self, org_id: str, role: Optional[str] = None
    ) -> List[ApprovalRecord]:
        """List pending approvals for an org"""
        factory = _get_async_session_local()
        async with factory() as db:
            query = (
                select(ApprovalRecord)
                .join(Task)
                .where(
                    and_(Task.org_id == org_id, ApprovalRecord.decision.is_(None))
                )
                .order_by(ApprovalRecord.sla_deadline.asc())
            )
            result = await db.execute(query)
            return list(result.scalars().all())


# ─── Notification Service ────────────────────────────────────────────

class NotificationService:
    """Real Notification Service (placeholder until messaging infra)"""

    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    async def send_approval_request(
        self, task_id: str, approval_id: str, message: str
    ) -> bool:
        """Send approval request notification"""
        self._log.append(
            {
                "type": "approval_request",
                "task_id": task_id,
                "approval_id": approval_id,
                "message": message,
                "sent_at": datetime.utcnow().isoformat(),
            }
        )
        return True

    async def send_notification(self, user_id: str, message: str) -> bool:
        """Send a notification to a user"""
        self._log.append(
            {
                "type": "user_notification",
                "user_id": user_id,
                "message": message,
                "sent_at": datetime.utcnow().isoformat(),
            }
        )
        return True


# ─── Event Service ───────────────────────────────────────────────────

class EventService:
    """Real Event Service"""

    async def create_event(
        self,
        task_id: str,
        event_type: str,
        details: Optional[Dict] = None,
        agent_id: Optional[str] = None,
    ) -> Event:
        """Create an event record"""
        factory = _get_async_session_local()
        async with factory() as db:
            import hashlib
            import json

            event_data = {
                "event_type": event_type,
                "task_id": task_id,
                "agent_id": agent_id,
                "data": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            canonical = json.dumps(event_data, sort_keys=True, default=str)
            signature = hashlib.sha256(canonical.encode()).hexdigest()
            event_id = signature[:64]

            event = Event(
                id=event_id,
                event_type=event_type,
                task_id=task_id,
                agent_id=agent_id,
                data=details or {},
                signature=signature,
                timestamp=datetime.utcnow(),
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            return event


# ─── Singletons ────────────────────────────────────────────────────────

task_service = TaskService()
approval_service = ApprovalService()
notification_service = NotificationService()
event_service = EventService()
