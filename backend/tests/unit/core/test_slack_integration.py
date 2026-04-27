"""Unit tests for Slack Integration"""
import pytest
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.services.slack_integration import SlackIntegration


class TestSlackIntegration:
    """Test Slack approval integration"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration(
            webhook_url="https://hooks.slack.com/test",
            bot_token="xoxb-test-token"
        )
    
    @pytest.mark.asyncio
    async def test_send_approval_request(self, slack):
        """Test sending approval request to Slack"""
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "method": "webhook"}
            
            result = await slack.send_approval_request(
                approval_id="approval-123",
                title="Delete production database",
                description="Agent wants to delete the production DB",
                requester_name="Claude Code",
                danger_level="critical",
                estimated_cost=500.0,
                channel="#approvals"
            )
            
            assert result["success"] is True
            mock_send.assert_called_once()
            
            # Check the message structure
            call_args = mock_send.call_args[0][0]
            assert call_args["channel"] == "#approvals"
            assert "🚨 Approval Request" in call_args["text"]
            assert "blocks" in call_args
    
    @pytest.mark.asyncio
    async def test_send_cost_alert(self, slack):
        """Test sending cost alert to Slack"""
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await slack.send_cost_alert(
                org_id="org-123",
                current_cost=850.0,
                budget_limit=1000.0,
                channel="#cost-alerts"
            )
            
            assert result["success"] is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0][0]
            assert "Budget Alert" in str(call_args)
            assert "$850.00" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_send_agent_status(self, slack):
        """Test sending agent status update"""
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await slack.send_agent_status(
                agent_name="claude-code-prod",
                status="waiting_approval",
                current_task="Deploy to production",
                channel="#agent-updates"
            )
            
            assert result["success"] is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0][0]
            assert "waiting_approval" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_handle_approve_button(self, slack):
        """Test handling approve button click"""
        
        payload = {
            "user": {"id": "U123456"},
            "actions": [
                {
                    "action_id": "approve_approval-123",
                    "value": "approval-123"
                }
            ]
        }
        
        result = await slack.handle_interactive_response(payload)
        
        assert result["approval_id"] == "approval-123"
        assert result["decision"] == "approved"
        assert result["approver_id"] == "U123456"
    
    @pytest.mark.asyncio
    async def test_handle_reject_button(self, slack):
        """Test handling reject button click"""
        
        payload = {
            "user": {"id": "U123456"},
            "actions": [
                {
                    "action_id": "reject_approval-123",
                    "value": "approval-123"
                }
            ]
        }
        
        result = await slack.handle_interactive_response(payload)
        
        assert result["approval_id"] == "approval-123"
        assert result["decision"] == "rejected"
        assert result["approver_id"] == "U123456"
    
    @pytest.mark.asyncio
    async def test_danger_level_emojis(self, slack):
        """Test different danger levels show correct emojis"""
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            levels = {
                "safe": "🟢",
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "critical": "🚨"
            }
            
            for level, expected_emoji in levels.items():
                await slack.send_approval_request(
                    approval_id=f"approval-{level}",
                    title="Test",
                    description="Test",
                    requester_name="Test",
                    danger_level=level,
                    estimated_cost=10.0
                )
                
                call_args = mock_send.call_args[0][0]
                assert expected_emoji in call_args["text"]
    
    def test_slack_initialization(self):
        """Test Slack integration initialization"""
        slack = SlackIntegration()
        assert slack.webhook_url is None
        assert slack.bot_token is None
        
        slack2 = SlackIntegration(
            webhook_url="https://hooks.slack.com/test",
            bot_token="xoxb-test"
        )
        assert slack2.webhook_url == "https://hooks.slack.com/test"
        assert slack2.bot_token == "xoxb-test"


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_no_slack_configured(self):
        """Test without Slack configuration"""
        slack = SlackIntegration()
        
        result = await slack.send_approval_request(
            approval_id="approval-123",
            title="Test",
            description="Test",
            requester_name="Test",
            danger_level="medium",
            estimated_cost=10.0
        )
        
        assert result["success"] is False
        assert "No Slack webhook" in result["error"]
    
    @pytest.mark.asyncio
    async def test_handle_unknown_action(self):
        """Test unknown action type"""
        slack = SlackIntegration()
        
        payload = {
            "user": {"id": "U123"},
            "actions": [
                {
                    "action_id": "unknown_action",
                    "value": "approval-123"
                }
            ]
        }
        
        result = await slack.handle_interactive_response(payload)
        
        assert result["decision"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_no_estimated_cost(self):
        """Test approval without cost estimate"""
        slack = SlackIntegration(webhook_url="https://hooks.slack.com/test")
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await slack.send_approval_request(
                approval_id="approval-123",
                title="Read file",
                description="Read /tmp/test.txt",
                requester_name="Test",
                danger_level="safe",
                estimated_cost=None
            )
            
            assert result["success"] is True
            call_args = mock_send.call_args[0][0]
            assert "N/A" in str(call_args)


class TestBudgetAlerts:
    """Test budget alert thresholds"""
    
    @pytest.mark.asyncio
    async def test_critical_budget_alert(self):
        """Test budget at 90%+ shows critical"""
        slack = SlackIntegration(webhook_url="https://hooks.slack.com/test")
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await slack.send_cost_alert(
                org_id="org-123",
                current_cost=950.0,
                budget_limit=1000.0
            )
            
            call_args = mock_send.call_args[0][0]
            assert "🔴" in str(call_args)
            assert "CRITICAL" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_warning_budget_alert(self):
        """Test budget at 75-89% shows warning"""
        slack = SlackIntegration(webhook_url="https://hooks.slack.com/test")
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await slack.send_cost_alert(
                org_id="org-123",
                current_cost=800.0,
                budget_limit=1000.0
            )
            
            call_args = mock_send.call_args[0][0]
            assert "🟠" in str(call_args)
            assert "WARNING" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_normal_budget_alert(self):
        """Test budget at 50-74% shows normal"""
        slack = SlackIntegration(webhook_url="https://hooks.slack.com/test")
        
        with patch.object(slack, '_send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True}
            
            result = await slack.send_cost_alert(
                org_id="org-123",
                current_cost=600.0,
                budget_limit=1000.0
            )
            
            call_args = mock_send.call_args[0][0]
            assert "🟡" in str(call_args)
