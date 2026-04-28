"""Unit tests for FleetOps Connection Layer"""
import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# sys.path removed - using PYTHONPATH

from app.core.connection_layer import (
    FleetOpsConnectionLayer,
    AgentRequest,
    request_agent_approval,
    approve_from_channel
)


class TestConnectionLayer:
    """Test the connection layer"""
    
    @pytest.fixture
    def connection(self):
        return FleetOpsConnectionLayer()
    
    @pytest.fixture
    def sample_request(self):
        return AgentRequest(
            agent_id="agent-123",
            agent_name="Claude Code",
            agent_type="claude_code",
            action="bash",
            arguments="rm -rf /tmp/data",
            file_path=None,
            environment="development",
            estimated_cost=10.0,
            org_id="org-123",
            requester_id="user-1"
        )
    
    @pytest.mark.asyncio
    async def test_auto_approve_safe_action(self, connection, sample_request):
        """Safe actions should be auto-approved"""
        
        safe_request = AgentRequest(
            agent_id="agent-123",
            agent_name="Claude Code",
            agent_type="claude_code",
            action="read",
            arguments="Read the file",
            file_path=None,
            environment="development",
            org_id="org-123"
        )
        
        result = await connection.process_agent_request(safe_request)
        
        assert result["status"] == "auto_approved"
        assert result["can_proceed"] is True
        assert result["danger_level"] in ["safe", "low"]
    
    @pytest.mark.asyncio
    async def test_high_danger_requires_approval(self, connection, sample_request):
        """High danger actions should require approval"""
        
        with patch.object(connection.approval_flow, 'request_approval', new_callable=AsyncMock) as mock_req:
            with patch.object(connection.approval_flow, 'wait_for_approval', new_callable=AsyncMock) as mock_wait:
                mock_req.return_value = {"id": "approval-123", "status": "pending"}
                mock_wait.return_value = {"status": "approved"}
                
                with patch.object(connection, '_notify_channels', new_callable=AsyncMock) as mock_notify:
                    result = await connection.process_agent_request(sample_request)
                    
                    assert result["status"] == "approved"
                    assert result["can_proceed"] is True
                    mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approval_rejected(self, connection, sample_request):
        """Rejected approvals should block agent"""
        
        with patch.object(connection.approval_flow, 'request_approval', new_callable=AsyncMock) as mock_req:
            with patch.object(connection.approval_flow, 'wait_for_approval', new_callable=AsyncMock) as mock_wait:
                mock_req.return_value = {"id": "approval-123", "status": "pending"}
                mock_wait.return_value = {"status": "rejected"}
                
                with patch.object(connection, '_notify_channels', new_callable=AsyncMock):
                    result = await connection.process_agent_request(sample_request)
                    
                    assert result["status"] == "rejected"
                    assert result["can_proceed"] is False
    
    @pytest.mark.asyncio
    async def test_approval_timeout(self, connection, sample_request):
        """Timed out approvals should block agent"""
        
        with patch.object(connection.approval_flow, 'request_approval', new_callable=AsyncMock) as mock_req:
            with patch.object(connection.approval_flow, 'wait_for_approval', new_callable=AsyncMock) as mock_wait:
                mock_req.return_value = {"id": "approval-123", "status": "pending"}
                mock_wait.return_value = {"status": "timeout"}
                
                with patch.object(connection, '_notify_channels', new_callable=AsyncMock):
                    result = await connection.process_agent_request(sample_request)
                    
                    assert result["status"] == "timeout"
                    assert result["can_proceed"] is False
    
    @pytest.mark.asyncio
    async def test_channel_routing_critical(self, connection, sample_request):
        """Critical danger should route to all channels"""
        
        critical_request = AgentRequest(
            agent_id="agent-123",
            agent_name="Claude Code",
            agent_type="claude_code",
            action="bash",
            arguments="rm -rf /app/.env.production",
            file_path="/app/.env.production",
            environment="production",
            org_id="org-123"
        )
        
        with patch.object(connection, '_notify_channels', new_callable=AsyncMock) as mock_notify:
            with patch.object(connection.approval_flow, 'request_approval', new_callable=AsyncMock):
                with patch.object(connection.approval_flow, 'wait_for_approval', new_callable=AsyncMock) as mock_wait:
                    mock_wait.return_value = {"status": "approved"}
                    
                    await connection.process_agent_request(critical_request)
                    
                    call_args = mock_notify.call_args[1]
                    assert call_args["danger"]["danger_level"] == "critical"
    
    @pytest.mark.asyncio
    async def test_slack_notification(self, connection, sample_request):
        """Slack should be notified for high danger"""
        
        with patch.object(connection.slack, 'send_approval_request', new_callable=AsyncMock) as mock_slack:
            with patch.object(connection.approval_flow, 'request_approval', new_callable=AsyncMock) as mock_req:
                with patch.object(connection.approval_flow, 'wait_for_approval', new_callable=AsyncMock) as mock_wait:
                    mock_req.return_value = {"id": "approval-123"}
                    mock_wait.return_value = {"status": "approved"}
                    
                    await connection.process_agent_request(sample_request)
                    
                    mock_slack.assert_called_once()
                    call_args = mock_slack.call_args[1]
                    assert call_args["danger_level"] in ["high", "critical"]
    
    @pytest.mark.asyncio
    async def test_handle_approval_response(self, connection):
        """Test handling approval response from any channel"""
        
        with patch.object(connection.approval_flow, 'approve', new_callable=AsyncMock) as mock_approve:
            mock_approve.return_value = {"status": "approved"}
            
            result = await connection.handle_approval_response(
                approval_id="approval-123",
                decision="approve",
                approver_id="user-1",
                comments="Looks good"
            )
            
            assert result["status"] == "success"
            assert result["decision"] == "approve"
            mock_approve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_channel_routing_rules(self, connection):
        """Test channel routing by danger level"""
        
        routing_cases = [
            ("safe", ["log"]),
            ("low", ["log"]),
            ("medium", ["dashboard", "email"]),
            ("high", ["slack", "dashboard", "email"]),
            ("critical", ["slack", "dashboard", "email", "cli"]),
        ]
        
        for danger_level, expected_channels in routing_cases:
            with patch.object(connection.slack, 'send_approval_request', new_callable=AsyncMock) as mock_slack:
                await connection._notify_channels(
                    approval_id="test-123",
                    request=AgentRequest(
                        agent_id="a", agent_name="Test", agent_type="test",
                        action="test", environment="dev"
                    ),
                    danger={"danger_level": danger_level},
                    approvers=["user-1"]
                )
                
                if "slack" in expected_channels:
                    mock_slack.assert_called_once()
                else:
                    mock_slack.assert_not_called()


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_request_agent_approval(self):
        """Test request_agent_approval convenience function"""
        
        with patch('app.core.connection_layer.connection_layer') as mock_layer:
            mock_layer.process_agent_request = AsyncMock()
            mock_layer.process_agent_request.return_value = {
                "status": "approved",
                "can_proceed": True
            }
            
            result = await request_agent_approval(
                agent_id="agent-1",
                agent_name="Claude Code",
                agent_type="claude_code",
                action="bash",
                arguments="rm -rf /tmp",
                environment="development"
            )
            
            assert result["status"] == "approved"
            mock_layer.process_agent_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_from_channel(self):
        """Test approve_from_channel convenience function"""
        
        with patch('app.core.connection_layer.connection_layer') as mock_layer:
            mock_layer.handle_approval_response = AsyncMock()
            mock_layer.handle_approval_response.return_value = {
                "status": "success",
                "decision": "approve"
            }
            
            result = await approve_from_channel(
                approval_id="approval-123",
                decision="approve",
                approver_id="user-1"
            )
            
            assert result["status"] == "success"
            mock_layer.handle_approval_response.assert_called_once()


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.fixture
    def connection(self):
        return FleetOpsConnectionLayer()
    
    @pytest.mark.asyncio
    async def test_empty_arguments(self, connection):
        """Handle empty arguments"""
        
        request = AgentRequest(
            agent_id="agent-1",
            agent_name="Test",
            agent_type="test",
            action="bash",
            arguments="",
            file_path=None,
            environment="development",
            org_id="org-123"
        )
        
        result = await connection.process_agent_request(request)
        
        # Should not crash
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_none_arguments(self, connection):
        """Handle None arguments"""
        
        request = AgentRequest(
            agent_id="agent-1",
            agent_name="Test",
            agent_type="test",
            action="bash",
            arguments=None,
            file_path=None,
            environment="development",
            org_id="org-123"
        )
        
        result = await connection.process_agent_request(request)
        
        # Should not crash
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_very_high_cost(self, connection):
        """Very high cost should escalate danger"""
        
        request = AgentRequest(
            agent_id="agent-1",
            agent_name="Test",
            agent_type="test",
            action="api",
            arguments="Generate report",
            file_path=None,
            environment="development",
            estimated_cost=500.0,
            org_id="org-123"
        )
        
        with patch.object(connection.approval_flow, 'request_approval', new_callable=AsyncMock):
            with patch.object(connection.approval_flow, 'wait_for_approval', new_callable=AsyncMock) as mock_wait:
                with patch.object(connection, '_notify_channels', new_callable=AsyncMock):
                    mock_wait.return_value = {"status": "approved"}
                    
                    result = await connection.process_agent_request(request)
                    
                    assert result["status"] == "approved"


class TestAgentRequest:
    """Test AgentRequest dataclass"""
    
    def test_create_request(self):
        """Test creating agent request"""
        request = AgentRequest(
            agent_id="agent-1",
            agent_name="Claude Code",
            agent_type="claude_code",
            action="bash",
            arguments="ls -la",
            file_path="/tmp",
            environment="development",
            estimated_cost=5.0,
            estimated_tokens=100,
            org_id="org-1",
            requester_id="user-1"
        )
        
        assert request.agent_id == "agent-1"
        assert request.agent_name == "Claude Code"
        assert request.action == "bash"
        assert request.estimated_cost == 5.0
    
    def test_default_values(self):
        """Test default values"""
        request = AgentRequest(
            agent_id="agent-1",
            agent_name="Test",
            agent_type="test",
            action="read",
            environment="development"
        )
        
        assert request.org_id == "default"
        assert request.requester_id == ""
        assert request.arguments is None
        assert request.file_path is None
