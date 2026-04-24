"""Human Approval Flow Integration for FleetOps

This module integrates the approval system into agent task execution.
Agents cannot proceed past approval checkpoints without human authorization.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio

from app.core.errors import (
    FleetOpsError,
    AuthorizationError,
    NotFoundError,
    ConflictError
)
from app.core.logging_config import log_agent_action, get_logger
from app.models.models import Task, TaskStatus, Approval, User

logger = get_logger("fleetops.approval_flow")


class ApprovalStage(Enum):
    """Stages where human approval may be required"""
    TASK_START = "task_start"           # Before agent begins work
    PLAN_REVIEW = "plan_review"         # After agent creates plan
    EXECUTION_STEP = "execution_step"   # Before each execution step
    EXTERNAL_ACTION = "external_action" # Before calling external APIs
    CODE_EXECUTION = "code_execution"   # Before running code
    FILE_WRITE = "file_write"          # Before writing files
    DEPLOYMENT = "deployment"          # Before deploying
    BUDGET_CHECK = "budget_check"      # Before spending budget
    COMPLETION = "completion"          # Before marking complete


class ApprovalRequirement(Enum):
    """When approval is required"""
    NEVER = "never"
    ALWAYS = "always"
    ON_HIGH_RISK = "on_high_risk"
    ON_COST_THRESHOLD = "on_cost_threshold"
    ON_EXTERNAL_ACTION = "on_external_action"


class ApprovalFlow:
    """Orchestrates human-in-the-loop approval for agent tasks"""
    
    # Default approval requirements by stage and risk level
    DEFAULT_REQUIREMENTS = {
        ApprovalStage.TASK_START: {
            "low": ApprovalRequirement.NEVER,
            "medium": ApprovalRequirement.NEVER,
            "high": ApprovalRequirement.ALWAYS,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.PLAN_REVIEW: {
            "low": ApprovalRequirement.NEVER,
            "medium": ApprovalRequirement.ON_HIGH_RISK,
            "high": ApprovalRequirement.ALWAYS,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.EXECUTION_STEP: {
            "low": ApprovalRequirement.NEVER,
            "medium": ApprovalRequirement.NEVER,
            "high": ApprovalRequirement.ON_COST_THRESHOLD,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.EXTERNAL_ACTION: {
            "low": ApprovalRequirement.ON_EXTERNAL_ACTION,
            "medium": ApprovalRequirement.ON_EXTERNAL_ACTION,
            "high": ApprovalRequirement.ALWAYS,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.CODE_EXECUTION: {
            "low": ApprovalRequirement.ON_HIGH_RISK,
            "medium": ApprovalRequirement.ALWAYS,
            "high": ApprovalRequirement.ALWAYS,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.FILE_WRITE: {
            "low": ApprovalRequirement.NEVER,
            "medium": ApprovalRequirement.ON_HIGH_RISK,
            "high": ApprovalRequirement.ALWAYS,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.DEPLOYMENT: {
            "low": ApprovalRequirement.ALWAYS,
            "medium": ApprovalRequirement.ALWAYS,
            "high": ApprovalRequirement.ALWAYS,
            "critical": ApprovalRequirement.ALWAYS,
        },
        ApprovalStage.BUDGET_CHECK: {
            "low": ApprovalRequirement.ON_COST_THRESHOLD,
            "medium": ApprovalRequirement.ON_COST_THRESHOLD,
            "high": ApprovalRequirement.ON_COST_THRESHOLD,
            "critical": ApprovalRequirement.ON_COST_THRESHOLD,
        },
        ApprovalStage.COMPLETION: {
            "low": ApprovalRequirement.NEVER,
            "medium": ApprovalRequirement.NEVER,
            "high": ApprovalRequirement.ON_HIGH_RISK,
            "critical": ApprovalRequirement.ALWAYS,
        },
    }
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._pending_approvals: Dict[str, asyncio.Event] = {}
        self._approval_callbacks: Dict[str, List[Callable]] = {}
    
    def is_approval_required(
        self,
        stage: ApprovalStage,
        risk_level: str = "low",
        custom_requirements: Optional[Dict] = None
    ) -> bool:
        """Check if approval is required for a given stage"""
        requirements = custom_requirements or self.DEFAULT_REQUIREMENTS
        
        stage_reqs = requirements.get(stage, {})
        requirement = stage_reqs.get(risk_level.lower(), ApprovalRequirement.NEVER)
        
        return requirement != ApprovalRequirement.NEVER
    
    async def request_approval(
        self,
        task_id: str,
        stage: ApprovalStage,
        title: str,
        description: str,
        requester_id: str,
        approver_ids: List[str],
        metadata: Optional[Dict] = None,
        timeout_hours: float = 24.0
    ) -> Dict[str, Any]:
        """Request human approval for a task stage"""
        
        approval_id = str(uuid.uuid4())
        deadline = datetime.utcnow() + timedelta(hours=timeout_hours)
        
        approval = {
            "id": approval_id,
            "task_id": task_id,
            "stage": stage.value,
            "title": title,
            "description": description,
            "requester_id": requester_id,
            "approver_ids": approver_ids,
            "status": "pending",
            "deadline": deadline.isoformat(),
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create async event for waiting
        self._pending_approvals[approval_id] = asyncio.Event()
        
        log_agent_action(
            agent_id=requester_id,
            action="approval_requested",
            task_id=task_id,
            details={
                "approval_id": approval_id,
                "stage": stage.value,
                "title": title
            }
        )
        
        logger.info(
            f"Approval requested: {title} for task {task_id}",
            extra={
                "approval_id": approval_id,
                "task_id": task_id,
                "stage": stage.value,
                "approvers": approver_ids
            }
        )
        
        # In production, this would:
        # 1. Save to database
        # 2. Send notifications (email, Slack, etc.)
        # 3. Update dashboard
        
        return approval
    
    async def wait_for_approval(
        self,
        approval_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Wait for human approval (blocking)"""
        
        event = self._pending_approvals.get(approval_id)
        if not event:
            raise NotFoundError("Approval", approval_id)
        
        try:
            if timeout:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                await event.wait()
        except asyncio.TimeoutError:
            return {
                "approval_id": approval_id,
                "status": "timeout",
                "message": "Approval timed out"
            }
        
        # Return result (in production, fetch from DB)
        return {
            "approval_id": approval_id,
            "status": "approved",  # or "rejected"
            "message": "Approval granted"
        }
    
    async def approve(
        self,
        approval_id: str,
        approver_id: str,
        decision: str = "approve",
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Human approves or rejects a pending approval"""
        
        event = self._pending_approvals.get(approval_id)
        if not event:
            raise NotFoundError("Approval", approval_id)
        
        if event.is_set():
            raise ConflictError("Approval already resolved")
        
        result = {
            "approval_id": approval_id,
            "status": decision,
            "approver_id": approver_id,
            "comments": comments,
            "resolved_at": datetime.utcnow().isoformat()
        }
        
        # Signal waiting coroutines
        event.set()
        
        log_agent_action(
            agent_id=approver_id,
            action=f"approval_{decision}",
            details={
                "approval_id": approval_id,
                "comments": comments
            }
        )
        
        logger.info(
            f"Approval {decision}: {approval_id} by {approver_id}",
            extra={
                "approval_id": approval_id,
                "decision": decision,
                "approver_id": approver_id
            }
        )
        
        # Trigger callbacks
        for callback in self._approval_callbacks.get(approval_id, []):
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
        
        return result
    
    async def check_stage_and_wait(
        self,
        task_id: str,
        stage: ApprovalStage,
        title: str,
        description: str,
        requester_id: str,
        approver_ids: List[str],
        risk_level: str = "low",
        timeout_hours: float = 24.0
    ) -> Dict[str, Any]:
        """Check if approval needed, request it, and wait"""
        
        # Check if approval is required
        if not self.is_approval_required(stage, risk_level):
            logger.debug(f"Approval not required for {stage.value} (risk: {risk_level})")
            return {
                "status": "not_required",
                "stage": stage.value,
                "message": f"Approval not required for {stage.value} at risk level {risk_level}"
            }
        
        # Request approval
        approval = await self.request_approval(
            task_id=task_id,
            stage=stage,
            title=title,
            description=description,
            requester_id=requester_id,
            approver_ids=approver_ids,
            timeout_hours=timeout_hours
        )
        
        # Wait for human
        logger.info(f"Waiting for approval {approval['id']}...")
        result = await self.wait_for_approval(
            approval_id=approval["id"],
            timeout=timeout_hours * 3600
        )
        
        if result["status"] == "timeout":
            raise AuthorizationError(
                f"Approval timed out for {stage.value}. Task cannot proceed."
            )
        
        if result["status"] != "approved":
            raise AuthorizationError(
                f"Approval rejected for {stage.value}. Task halted."
            )
        
        return result
    
    def on_approval_resolved(self, approval_id: str, callback: Callable):
        """Register a callback for when approval is resolved"""
        if approval_id not in self._approval_callbacks:
            self._approval_callbacks[approval_id] = []
        self._approval_callbacks[approval_id].append(callback)
    
    def get_pending_approvals(self, task_id: Optional[str] = None) -> List[Dict]:
        """Get all pending approvals"""
        pending = []
        for approval_id, event in self._pending_approvals.items():
            if not event.is_set():
                pending.append({
                    "approval_id": approval_id,
                    "status": "pending"
                })
        return pending


# Global instance
approval_flow = ApprovalFlow()


# ─── Convenience Functions ─────────────────────────────────────────────

async def require_approval(
    task_id: str,
    stage: ApprovalStage,
    title: str,
    description: str,
    requester_id: str,
    approver_ids: List[str],
    risk_level: str = "low",
    timeout_hours: float = 24.0
) -> Dict[str, Any]:
    """Convenience function to require and wait for approval"""
    return await approval_flow.check_stage_and_wait(
        task_id=task_id,
        stage=stage,
        title=title,
        description=description,
        requester_id=requester_id,
        approver_ids=approver_ids,
        risk_level=risk_level,
        timeout_hours=timeout_hours
    )
