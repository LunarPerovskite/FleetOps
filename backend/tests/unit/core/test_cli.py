"""Unit tests for FleetOps CLI"""
import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock

from cli import app
from typer.testing import CliRunner

runner = CliRunner()


class TestCLIStatus:
    """Test status command"""
    
    @patch('cli.get_client')
    def test_status_command(self, mock_get_client):
        """Test status command shows system status"""
        mock_client = MagicMock()
        mock_client.get_status = AsyncMock(return_value={
            "status": "healthy",
            "version": "1.0.0",
            "agents": 5,
            "pending_approvals": 2,
            "total_cost_today": 47.83
        })
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "Status" in result.output
        assert "HEALTHY" in result.output.upper()
    
    @patch('cli.get_client')
    def test_status_output_contains_metrics(self, mock_get_client):
        """Status should show agents, approvals, costs"""
        mock_client = MagicMock()
        mock_client.get_status = AsyncMock(return_value={
            "status": "healthy",
            "agents": 5,
            "pending_approvals": 2,
            "total_cost_today": 47.83
        })
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["status"])
        
        assert "Agents:" in result.output
        assert "Pending Approvals:" in result.output
        assert "Cost Today:" in result.output
    
    def test_status_when_unavailable(self):
        """Status shows unavailable when server is down"""
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 1
        assert "not available" in result.output.lower()


class TestCLIList:
    """Test list command"""
    
    @patch('cli.get_client')
    def test_list_command(self, mock_get_client):
        """Test list command shows pending approvals"""
        mock_client = MagicMock()
        mock_client.get_pending = AsyncMock(return_value=[
            {"id": "apr-001", "agent_name": "claude-code", "action": "delete", "danger_level": "high", "estimated_cost": 0.0},
            {"id": "apr-002", "agent_name": "roo-code", "action": "write", "danger_level": "critical", "estimated_cost": 0.0}
        ])
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["approvals"])
        
        assert result.exit_code == 0
        assert "Approvals" in result.output
    
    @patch('cli.get_client')
    def test_list_shows_approvals(self, mock_get_client):
        """List should show approval details"""
        mock_client = MagicMock()
        mock_client.get_pending = AsyncMock(return_value=[
            {"id": "apr-001", "agent_name": "claude-code", "action": "delete", "danger_level": "high", "estimated_cost": 0.0}
        ])
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["approvals"])
        
        assert result.exit_code == 0
        assert "apr-001" in result.output
        assert "claude-code" in result.output
    
    @patch('cli.get_client')
    def test_list_shows_danger_levels(self, mock_get_client):
        """List should show colored danger levels"""
        mock_client = MagicMock()
        mock_client.get_pending = AsyncMock(return_value=[
            {"id": "apr-001", "agent_name": "claude-code", "action": "delete", "danger_level": "high", "estimated_cost": 0.0},
            {"id": "apr-002", "agent_name": "roo-code", "action": "write", "danger_level": "critical", "estimated_cost": 0.0}
        ])
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["approvals"])
        
        assert result.exit_code == 0
        # Check for ANSI color codes (rich adds color)
        assert "\x1b[" in result.output or any(emoji in result.output for emoji in ["🔴", "🚨", "🟠"])


class TestCLIApprove:
    """Test approve command"""
    
    @patch('cli.get_client')
    def test_approve_command(self, mock_get_client):
        """Test approve command"""
        mock_client = MagicMock()
        mock_client.approve = AsyncMock(return_value={"status": "success", "message": "Approved"})
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["approve", "apr-001", "--force"])
        
        assert result.exit_code == 0
        assert "Approved" in result.output or "approved" in result.output.lower()
        assert "apr-001" in result.output
    
    @patch('cli.get_client')
    def test_approve_with_scope(self, mock_get_client):
        """Test approve with different scopes"""
        mock_client = MagicMock()
        mock_client.approve = AsyncMock(return_value={"status": "success"})
        mock_get_client.return_value = mock_client
        
        for scope in ["once", "session", "workspace", "always"]:
            result = runner.invoke(app, ["approve", "apr-001", "--scope", scope, "--force"])
            
            assert result.exit_code == 0
    
    def test_approve_invalid_scope(self):
        """Test approve with invalid scope"""
        result = runner.invoke(app, ["approve", "apr-001", "--scope", "invalid", "--force"])
        
        assert result.exit_code != 0 or "Invalid scope" in result.output
    
    @patch('cli.get_client')
    def test_approve_confirmation_prompt(self, mock_get_client):
        """Test approve without --force prompts for confirmation"""
        mock_client = MagicMock()
        mock_client.approve = AsyncMock(return_value={"status": "success"})
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["approve", "apr-001"], input="y\n")
        
        # Should either succeed or show prompt
        assert result.exit_code == 0 or "Approve" in result.output or "confirm" in result.output.lower()


class TestCLIReject:
    """Test reject command"""
    
    @patch('cli.get_client')
    def test_reject_command(self, mock_get_client):
        """Test reject command"""
        mock_client = MagicMock()
        mock_client.reject = AsyncMock(return_value={"status": "success", "message": "Rejected"})
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["reject", "apr-001", "--force"])
        
        assert result.exit_code == 0
        assert "Rejected" in result.output or "rejected" in result.output.lower()
    
    @patch('cli.get_client')
    def test_reject_with_comments(self, mock_get_client):
        """Test reject with comments"""
        mock_client = MagicMock()
        mock_client.reject = AsyncMock(return_value={"status": "success"})
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["reject", "apr-001", "--comments", "Too risky", "--force"])
        
        assert result.exit_code == 0


class TestCLIAgents:
    """Test agents command"""
    
    def test_agents_command(self):
        """Test agents command"""
        result = runner.invoke(app, ["agents"])
        
        assert result.exit_code == 0
        assert "Agents" in result.output
        assert "claude-code" in result.output
    
    def test_agents_shows_status(self):
        """Agents should show status"""
        result = runner.invoke(app, ["agents"])
        
        assert result.exit_code == 0
        assert "running" in result.output or "🟢" in result.output


class TestCLICosts:
    """Test costs command"""
    
    def test_costs_command(self):
        """Test costs command"""
        result = runner.invoke(app, ["costs"])
        
        assert result.exit_code == 0
        assert "Cost" in result.output or "cost" in result.output.lower()
        assert "$47.83" in result.output
    
    def test_costs_with_breakdown(self):
        """Test costs with breakdown"""
        result = runner.invoke(app, ["costs", "--breakdown"])
        
        assert result.exit_code == 0
        assert "Cost" in result.output or "cost" in result.output.lower()
    
    def test_costs_shows_budget_bar(self):
        """Costs should show visual budget bar"""
        result = runner.invoke(app, ["costs"])
        
        assert result.exit_code == 0
        assert "█" in result.output or "Usage:" in result.output


class TestCLIConfig:
    """Test config command"""
    
    def test_config_command(self):
        """Test config command shows config"""
        result = runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        assert "FleetOps" in result.output
    
    def test_config_shows_api_url(self):
        """Config should show API URL"""
        result = runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        assert "API" in result.output or "URL" in result.output


class TestCLIHelp:
    """Test help output"""
    
    def test_main_help(self):
        """Test main help message"""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "FleetOps" in result.output
    
    def test_command_help(self):
        """Test individual command help"""
        commands = ["status", "approvals", "approve", "reject", "agents", "costs", "config"]
        
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.output or "Options:" in result.output


class TestCLIColors:
    """Test colored output"""
    
    @patch('cli.get_client')
    def test_danger_colors(self, mock_get_client):
        """Different danger levels should have different colors"""
        mock_client = MagicMock()
        mock_client.get_pending = AsyncMock(return_value=[
            {"id": "apr-001", "agent_name": "claude", "action": "delete", "danger_level": "high", "estimated_cost": 0.0},
            {"id": "apr-002", "agent_name": "roo", "action": "write", "danger_level": "critical", "estimated_cost": 0.0}
        ])
        mock_get_client.return_value = mock_client
        
        result = runner.invoke(app, ["approvals"])
        
        # Should contain ANSI color codes (rich adds color) or emojis
        assert result.exit_code == 0
        assert "\x1b[" in result.output or any(emoji in result.output for emoji in ["🔴", "🚨", "🟠", "🟢", "🟡"])
