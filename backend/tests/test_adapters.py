"""Tests for Agent Adapters

Comprehensive tests for OpenClaw, Hermes, and Personal Agent adapters.
Tests API communication, error handling, and governance features.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.adapters.openclaw_adapter import OpenClawAdapter, OpenClawExecutionStatus
from app.adapters.hermes_adapter import HermesAdapter, HermesExecutionStatus
from app.adapters.personal_agent_adapter import PersonalAgentAdapter, AgentType


# ═══════════════════════════════════════
# OPENCLAW ADAPTER TESTS
# ═══════════════════════════════════════

class TestOpenClawAdapter:
    """Test suite for OpenClaw adapter"""
    
    @pytest.fixture
    async def adapter(self):
        """Create adapter with mocked HTTP client"""
        adapter = OpenClawAdapter()
        # Mock the HTTP client
        adapter.client = AsyncMock()
        yield adapter
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, adapter):
        """Test successful session creation"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "sess_123",
            "status": "created",
            "task_id": "task_123"
        }
        mock_response.status_code = 201
        adapter.client.post.return_value = mock_response
        
        result = await adapter.create_session(
            task_id="task_123",
            instructions="Test task"
        )
        
        assert result["status"] == "created"
        assert result["session_id"] == "sess_123"
        adapter.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_http_error(self, adapter):
        """Test session creation with HTTP error"""
        import httpx
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        error = httpx.HTTPStatusError("Server Error", 
                                      request=MagicMock(), 
                                      response=mock_response)
        adapter.client.post.side_effect = error
        
        result = await adapter.create_session(
            task_id="task_123",
            instructions="Test task"
        )
        
        assert result["status"] == "error"
        assert "500" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_session_timeout(self, adapter):
        """Test session creation with timeout"""
        import httpx
        
        adapter.client.post.side_effect = httpx.TimeoutException("Timeout")
        
        result = await adapter.create_session(
            task_id="task_123",
            instructions="Test task"
        )
        
        assert result["status"] == "error"
        assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_session_status(self, adapter):
        """Test getting session status"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "running",
            "current_step": 3,
            "total_steps": 10,
            "output": "Working on it..."
        }
        adapter.client.get.return_value = mock_response
        
        result = await adapter.get_session_status("sess_123")
        
        assert result["status"] == "running"
        assert result["current_step"] == 3
        assert result["awaiting_approval"] == False
    
    @pytest.mark.asyncio
    async def test_awaiting_approval_detection(self, adapter):
        """Test detection of awaiting approval state"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "awaiting_approval",
            "current_step": 5
        }
        adapter.client.get.return_value = mock_response
        
        result = await adapter.get_session_status("sess_123")
        
        assert result["awaiting_approval"] == True
    
    @pytest.mark.asyncio
    async def test_submit_human_approval(self, adapter):
        """Test submitting human approval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "approved", "next_step": 6}
        adapter.client.post.return_value = mock_response
        
        result = await adapter.submit_human_approval(
            session_id="sess_123",
            step_id="step_5",
            decision="approve",
            comments="Looks good"
        )
        
        assert result["status"] == "success"
        assert result["decision_recorded"] == True
    
    @pytest.mark.asyncio
    async def test_risk_assessment_high(self, adapter):
        """Test high-risk action detection"""
        step = {
            "action_type": "delete_file",
            "affected_files": ["production/config.yml"]
        }
        
        risk = adapter._assess_risk(step)
        assert risk == "high"
        assert adapter._can_auto_approve(step) == False
    
    @pytest.mark.asyncio
    async def test_risk_assessment_low(self, adapter):
        """Test low-risk action detection"""
        step = {
            "action_type": "read_file",
            "affected_files": ["docs/readme.md"]
        }
        
        risk = adapter._assess_risk(step)
        assert risk == "low"
        assert adapter._can_auto_approve(step) == True
    
    @pytest.mark.asyncio
    async def test_cancel_session(self, adapter):
        """Test session cancellation"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        adapter.client.post.return_value = mock_response
        
        result = await adapter.cancel_session("sess_123", "User cancelled")
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_logs(self, adapter):
        """Test getting session logs"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "logs": [
                {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "Started"},
                {"timestamp": "2024-01-01T00:01:00", "level": "INFO", "message": "Completed"}
            ]
        }
        adapter.client.get.return_value = mock_response
        
        logs = await adapter.get_session_logs("sess_123")
        
        assert len(logs) == 2
        assert logs[0]["message"] == "Started"


# ═══════════════════════════════════════
# HERMES ADAPTER TESTS
# ═══════════════════════════════════════

class TestHermesAdapter:
    """Test suite for Hermes adapter"""
    
    @pytest.fixture
    async def adapter(self):
        adapter = HermesAdapter()
        adapter.client = AsyncMock()
        yield adapter
    
    @pytest.mark.asyncio
    async def test_submit_task_success(self, adapter):
        """Test successful task submission"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "execution_id": "exec_123",
            "estimated_duration": 120,
            "status": "queued"
        }
        adapter.client.post.return_value = mock_response
        
        result = await adapter.submit_task(
            task_id="task_123",
            instructions="Test task"
        )
        
        assert result["status"] == "submitted"
        assert result["execution_id"] == "exec_123"
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, adapter):
        """Test getting execution status"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "executing",
            "progress": 45,
            "current_step": "data_processing"
        }
        adapter.client.get.return_value = mock_response
        
        result = await adapter.get_execution_status("exec_123")
        
        assert result["status"] == "executing"
        assert result["progress"] == 45
    
    @pytest.mark.asyncio
    async def test_approve_step(self, adapter):
        """Test approving a step"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "approved", "continuing": True}
        adapter.client.post.return_value = mock_response
        
        result = await adapter.approve_step(
            execution_id="exec_123",
            step_id="step_3",
            approved=True,
            comments="Approved by operator"
        )
        
        assert result["status"] == "success"
        assert result["approved"] == True
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, adapter):
        """Test getting pending approvals"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "approvals": [
                {
                    "step_id": "step_2",
                    "description": "Send email to customer",
                    "risk_level": "medium"
                }
            ]
        }
        adapter.client.get.return_value = mock_response
        
        approvals = await adapter.get_pending_approvals("exec_123")
        
        assert len(approvals) == 1
        assert approvals[0]["step_id"] == "step_2"
    
    @pytest.mark.asyncio
    async def test_provide_feedback(self, adapter):
        """Test providing feedback"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        adapter.client.post.return_value = mock_response
        
        result = await adapter.provide_feedback(
            execution_id="exec_123",
            feedback="Great work, very accurate",
            rating=5
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, adapter):
        """Test cancelling execution"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        adapter.client.post.return_value = mock_response
        
        result = await adapter.cancel_execution("exec_123")
        
        assert result == True


# ═══════════════════════════════════════
# PERSONAL AGENT ADAPTER TESTS
# ═══════════════════════════════════════

class TestPersonalAgentAdapter:
    """Test suite for unified personal agent adapter"""
    
    @pytest.mark.asyncio
    async def test_openclaw_execution(self):
        """Test executing with OpenClaw through unified adapter"""
        adapter = PersonalAgentAdapter("openclaw")
        
        # Mock the internal adapter
        adapter._adapter = AsyncMock()
        adapter._adapter.create_session.return_value = {
            "status": "created",
            "session_id": "sess_123"
        }
        
        result = await adapter.execute_task(
            task_id="task_123",
            instructions="Test task"
        )
        
        assert result["status"] == "executing"
        assert result["agent_type"] == "openclaw"
        assert result["session_id"] == "sess_123"
    
    @pytest.mark.asyncio
    async def test_hermes_execution(self):
        """Test executing with Hermes through unified adapter"""
        adapter = PersonalAgentAdapter("hermes")
        
        adapter._adapter = AsyncMock()
        adapter._adapter.submit_task.return_value = {
            "status": "submitted",
            "execution_id": "exec_123"
        }
        
        result = await adapter.execute_task(
            task_id="task_123",
            instructions="Test task"
        )
        
        assert result["status"] == "executing"
        assert result["agent_type"] == "hermes"
        assert result["execution_id"] == "exec_123"
    
    @pytest.mark.asyncio
    async def test_get_status_openclaw(self):
        """Test getting status for OpenClaw"""
        adapter = PersonalAgentAdapter("openclaw")
        adapter._adapter = AsyncMock()
        adapter._adapter.get_session_status.return_value = {
            "status": "running",
            "awaiting_approval": False
        }
        
        result = await adapter.get_status("sess_123")
        
        assert result["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self):
        """Test getting pending approvals"""
        adapter = PersonalAgentAdapter("openclaw")
        adapter._adapter = AsyncMock()
        adapter._adapter.get_session_status.return_value = {
            "status": "awaiting_approval",
            "current_step": "step_3"
        }
        adapter._adapter.get_step_details.return_value = {
            "status": "success",
            "step": {
                "id": "step_3",
                "description": "Update database",
                "action_type": "file_edit",
                "risk_level": "medium",
                "can_auto_approve": False
            }
        }
        
        approvals = await adapter.get_pending_approvals("sess_123")
        
        assert len(approvals) == 1
        assert approvals[0]["risk_level"] == "medium"
    
    @pytest.mark.asyncio
    async def test_approve_openclaw(self):
        """Test approving with OpenClaw"""
        adapter = PersonalAgentAdapter("openclaw")
        adapter._adapter = AsyncMock()
        adapter._adapter.submit_human_approval.return_value = {
            "status": "success"
        }
        
        result = await adapter.approve(
            execution_id="sess_123",
            step_id="step_3",
            decision="approve",
            comments="Looks good"
        )
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_approve_hermes(self):
        """Test approving with Hermes"""
        adapter = PersonalAgentAdapter("hermes")
        adapter._adapter = AsyncMock()
        adapter._adapter.approve_step.return_value = {
            "status": "success"
        }
        
        result = await adapter.approve(
            execution_id="exec_123",
            step_id="step_2",
            decision="approve"
        )
        
        assert result["status"] == "success"
    
    def test_get_capabilities(self):
        """Test getting agent capabilities"""
        adapter = PersonalAgentAdapter("openclaw")
        capabilities = adapter.get_capabilities()
        
        assert "session_based_execution" in capabilities
        assert "step_by_step_approval" in capabilities
    
    def test_unsupported_agent(self):
        """Test handling unsupported agent type"""
        adapter = PersonalAgentAdapter("unsupported")
        
        assert adapter._adapter is not None  # Falls back to custom adapter
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in unified adapter"""
        adapter = PersonalAgentAdapter("openclaw")
        adapter._adapter = AsyncMock()
        adapter._adapter.create_session.side_effect = Exception("Connection failed")
        
        result = await adapter.execute_task(
            task_id="task_123",
            instructions="Test"
        )
        
        assert result["status"] == "error"
        assert "Connection failed" in result["error"]


# ═══════════════════════════════════════
# AGENT EXECUTION SERVICE TESTS
# ═══════════════════════════════════════

class TestAgentExecutionService:
    """Test suite for agent execution service"""
    
    @pytest.fixture
    def service(self):
        from app.services.agent_execution_service import AgentExecutionService
        return AgentExecutionService()
    
    @pytest.mark.asyncio
    async def test_execute_task_not_found(self, service):
        """Test execution with non-existent task"""
        with patch('app.services.agent_execution_service.task_service') as mock_task:
            mock_task.get_task.return_value = None
            
            result = await service.execute_task("nonexistent", "openclaw")
            
            assert result["status"] == "error"
            assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, service):
        """Test cancelling execution"""
        # Setup active execution
        service._active_executions["task_123"] = {
            "execution_id": "exec_123",
            "agent_type": "openclaw",
            "started_at": datetime.utcnow()
        }
        
        with patch('app.services.agent_execution_service.PersonalAgentAdapter') as mock_adapter:
            mock_instance = AsyncMock()
            mock_instance.cancel.return_value = True
            mock_adapter.return_value = mock_instance
            
            result = await service.cancel_execution("task_123", "Test cancel")
            
            assert result["status"] == "success"
            assert "task_123" not in service._active_executions


# ═══════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════

class TestAdapterIntegration:
    """Integration-style tests for adapter ecosystem"""
    
    @pytest.mark.asyncio
    async def test_full_openclaw_flow(self):
        """Test complete OpenClaw execution flow"""
        adapter = OpenClawAdapter()
        adapter.client = AsyncMock()
        
        # 1. Create session
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "sess_123", "status": "created"}
        adapter.client.post.return_value = mock_response
        
        result = await adapter.create_session("task_1", "Test task")
        session_id = result["session_id"]
        
        # 2. Check status - running
        mock_response.json.return_value = {
            "status": "running",
            "current_step": 2
        }
        adapter.client.get.return_value = mock_response
        
        status = await adapter.get_session_status(session_id)
        assert status["status"] == "running"
        
        # 3. Check status - awaiting approval
        mock_response.json.return_value = {
            "status": "awaiting_approval",
            "current_step": 3
        }
        
        status = await adapter.get_session_status(session_id)
        assert status["awaiting_approval"] == True
        
        # 4. Get step details
        mock_response.json.return_value = {
            "id": "step_3",
            "description": "Send notification email",
            "action_type": "api_call",
            "affected_files": [],
            "proposed_changes": {}
        }
        
        details = await adapter.get_step_details(session_id, "step_3")
        assert details["status"] == "success"
        assert details["step"]["risk_level"] == "medium"
        
        # 5. Submit approval
        mock_response.json.return_value = {"status": "approved", "next_step": 4}
        adapter.client.post.return_value = mock_response
        
        approval = await adapter.submit_human_approval(
            session_id, "step_3", "approve", "Approved by test"
        )
        assert approval["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_full_hermes_flow(self):
        """Test complete Hermes execution flow"""
        adapter = HermesAdapter()
        adapter.client = AsyncMock()
        
        # 1. Submit task
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "execution_id": "exec_123",
            "estimated_duration": 60
        }
        adapter.client.post.return_value = mock_response
        
        result = await adapter.submit_task("task_1", "Analyze data")
        exec_id = result["execution_id"]
        
        # 2. Check progress
        mock_response.json.return_value = {
            "status": "executing",
            "progress": 75,
            "current_step": "analysis"
        }
        adapter.client.get.return_value = mock_response
        
        status = await adapter.get_execution_status(exec_id)
        assert status["progress"] == 75
        
        # 3. Get pending approvals
        mock_response.json.return_value = {
            "approvals": [
                {
                    "step_id": "step_2",
                    "description": "Generate report",
                    "risk_level": "low"
                }
            ]
        }
        
        approvals = await adapter.get_pending_approvals(exec_id)
        assert len(approvals) == 1
        
        # 4. Approve
        mock_response.json.return_value = {"status": "approved"}
        adapter.client.post.return_value = mock_response
        
        result = await adapter.approve_step(exec_id, "step_2", True)
        assert result["status"] == "success"
        
        # 5. Get final result
        mock_response.json.return_value = {
            "status": "completed",
            "output": "Analysis complete",
            "artifacts": [{"type": "report", "url": "/reports/1"}]
        }
        
        status = await adapter.get_execution_status(exec_id)
        assert status["status"] == "completed"


# ═══════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
