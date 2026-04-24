"""Unit tests for human approval flow."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.core.approval_flow import (
    ApprovalFlow,
    ApprovalStage,
    ApprovalRequirement,
    require_approval,
    approval_flow
)
from app.core.errors import NotFoundError, ConflictError, AuthorizationError


class TestApprovalFlow:
    """Test the ApprovalFlow class."""

    @pytest.fixture
    def flow(self):
        return ApprovalFlow()

    def test_is_approval_required_low_risk(self, flow):
        """Test low risk tasks need less approval."""
        assert flow.is_approval_required(
            ApprovalStage.TASK_START, "low"
        ) is False
        
        assert flow.is_approval_required(
            ApprovalStage.DEPLOYMENT, "low"
        ) is True  # Deployment always requires approval

    def test_is_approval_required_high_risk(self, flow):
        """Test high risk tasks need more approval."""
        assert flow.is_approval_required(
            ApprovalStage.TASK_START, "high"
        ) is True
        
        assert flow.is_approval_required(
            ApprovalStage.PLAN_REVIEW, "high"
        ) is True

    def test_is_approval_required_critical(self, flow):
        """Test critical tasks always need approval."""
        for stage in ApprovalStage:
            if stage != ApprovalStage.TASK_START:
                assert flow.is_approval_required(stage, "critical") is True

    def test_custom_requirements(self, flow):
        """Test custom approval requirements."""
        custom = {
            ApprovalStage.TASK_START: {
                "low": ApprovalRequirement.ALWAYS
            }
        }
        
        assert flow.is_approval_required(
            ApprovalStage.TASK_START, "low", custom
        ) is True

    @pytest.mark.asyncio
    async def test_request_approval(self, flow):
        """Test requesting approval."""
        approval = await flow.request_approval(
            task_id="task-123",
            stage=ApprovalStage.EXTERNAL_ACTION,
            title="Call external API",
            description="Agent wants to call OpenAI API",
            requester_id="agent-1",
            approver_ids=["user-1"]
        )
        
        assert approval["task_id"] == "task-123"
        assert approval["stage"] == "external_action"
        assert approval["status"] == "pending"
        assert "id" in approval
        assert "deadline" in approval

    @pytest.mark.asyncio
    async def test_approve_and_wait(self, flow):
        """Test approval workflow: request then approve."""
        # Request approval
        approval = await flow.request_approval(
            task_id="task-123",
            stage=ApprovalStage.FILE_WRITE,
            title="Write file",
            description="Agent wants to write to /tmp/test.txt",
            requester_id="agent-1",
            approver_ids=["user-1"]
        )
        
        approval_id = approval["id"]
        
        # Approve in background
        async def delayed_approve():
            await asyncio.sleep(0.1)
            await flow.approve(approval_id, "user-1", "approve")
        
        # Start approval and wait
        approve_task = asyncio.create_task(delayed_approve())
        result = await flow.wait_for_approval(approval_id, timeout=5.0)
        await approve_task
        
        assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_reject_approval(self, flow):
        """Test rejection workflow."""
        approval = await flow.request_approval(
            task_id="task-123",
            stage=ApprovalStage.DEPLOYMENT,
            title="Deploy",
            description="Agent wants to deploy",
            requester_id="agent-1",
            approver_ids=["user-1"]
        )
        
        # Reject
        result = await flow.approve(
            approval["id"], "user-1", "reject", "Too risky"
        )
        
        assert result["status"] == "reject"
        assert result["comments"] == "Too risky"

    @pytest.mark.asyncio
    async def test_wait_timeout(self, flow):
        """Test waiting with timeout."""
        approval = await flow.request_approval(
            task_id="task-123",
            stage=ApprovalStage.EXTERNAL_ACTION,
            title="Call API",
            description="Call external API",
            requester_id="agent-1",
            approver_ids=["user-1"]
        )
        
        # Wait with short timeout (no one approves)
        result = await flow.wait_for_approval(
            approval["id"], timeout=0.1
        )
        
        assert result["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_double_approve_error(self, flow):
        """Test double approval raises error."""
        approval = await flow.request_approval(
            task_id="task-123",
            stage=ApprovalStage.FILE_WRITE,
            title="Write file",
            description="Write file",
            requester_id="agent-1",
            approver_ids=["user-1"]
        )
        
        # First approve
        await flow.approve(approval["id"], "user-1", "approve")
        
        # Second approve should fail
        with pytest.raises(ConflictError):
            await flow.approve(approval["id"], "user-1", "approve")

    @pytest.mark.asyncio
    async def test_wait_nonexistent_approval(self, flow):
        """Test waiting for non-existent approval."""
        with pytest.raises(NotFoundError):
            await flow.wait_for_approval("nonexistent", timeout=0.1)

    @pytest.mark.asyncio
    async def test_check_stage_and_wait_not_required(self, flow):
        """Test stage that doesn't require approval."""
        result = await flow.check_stage_and_wait(
            task_id="task-123",
            stage=ApprovalStage.TASK_START,
            title="Start",
            description="Start task",
            requester_id="agent-1",
            approver_ids=["user-1"],
            risk_level="low"
        )
        
        assert result["status"] == "not_required"

    @pytest.mark.asyncio
    async def test_check_stage_and_wait_timeout(self, flow):
        """Test required approval that times out."""
        with pytest.raises(AuthorizationError):
            await flow.check_stage_and_wait(
                task_id="task-123",
                stage=ApprovalStage.DEPLOYMENT,
                title="Deploy",
                description="Deploy app",
                requester_id="agent-1",
                approver_ids=["user-1"],
                risk_level="high",
                timeout_hours=0.001  # Very short for testing
            )

    @pytest.mark.asyncio
    async def test_callback(self, flow):
        """Test approval callback."""
        callback_called = False
        callback_result = None
        
        async def my_callback(result):
            nonlocal callback_called, callback_result
            callback_called = True
            callback_result = result
        
        approval = await flow.request_approval(
            task_id="task-123",
            stage=ApprovalStage.FILE_WRITE,
            title="Write",
            description="Write file",
            requester_id="agent-1",
            approver_ids=["user-1"]
        )
        
        flow.on_approval_resolved(approval["id"], my_callback)
        
        await flow.approve(approval["id"], "user-1", "approve")
        
        # Give callback time to execute
        await asyncio.sleep(0.1)
        
        assert callback_called is True
        assert callback_result["status"] == "approve"

    def test_get_pending_approvals(self, flow):
        """Test listing pending approvals."""
        # Should start empty
        pending = flow.get_pending_approvals()
        assert isinstance(pending, list)


class TestApprovalStage:
    """Test ApprovalStage enum."""

    def test_all_stages(self):
        """Test all stages exist."""
        stages = list(ApprovalStage)
        assert len(stages) > 0
        assert ApprovalStage.TASK_START in stages
        assert ApprovalStage.DEPLOYMENT in stages
        assert ApprovalStage.BUDGET_CHECK in stages

    def test_stage_values(self):
        """Test stage values."""
        assert ApprovalStage.TASK_START.value == "task_start"
        assert ApprovalStage.PLAN_REVIEW.value == "plan_review"
        assert ApprovalStage.EXECUTION_STEP.value == "execution_step"


class TestApprovalRequirement:
    """Test ApprovalRequirement enum."""

    def test_requirements(self):
        """Test all requirements."""
        assert ApprovalRequirement.NEVER.value == "never"
        assert ApprovalRequirement.ALWAYS.value == "always"
        assert ApprovalRequirement.ON_HIGH_RISK.value == "on_high_risk"
        assert ApprovalRequirement.ON_COST_THRESHOLD.value == "on_cost_threshold"


class TestGlobalInstance:
    """Test the global approval_flow instance."""

    def test_global_instance_exists(self):
        """Test global instance is available."""
        assert approval_flow is not None
        assert isinstance(approval_flow, ApprovalFlow)

    @pytest.mark.asyncio
    async def test_require_approval_convenience(self):
        """Test the convenience function."""
        # Low risk task start should not require approval
        result = await require_approval(
            task_id="task-123",
            stage=ApprovalStage.TASK_START,
            title="Start",
            description="Start task",
            requester_id="agent-1",
            approver_ids=["user-1"],
            risk_level="low"
        )
        
        assert result["status"] == "not_required"
