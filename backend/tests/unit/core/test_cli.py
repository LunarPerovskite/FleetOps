"""Unit tests for FleetOps CLI"""
import pytest
import sys
from io import StringIO
from unittest.mock import patch, AsyncMock

sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from cli import app
from typer.testing import CliRunner

runner = CliRunner()


class TestCLIStatus:
    """Test status command"""
    
    def test_status_command(self):
        """Test status command shows system status"""
        result = runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "FleetOps Status" in result.output
        assert "HEALTHY" in result.output
    
    def test_status_output_contains_metrics(self):
        """Status should show agents, approvals, costs"""
        result = runner.invoke(app, ["status"])
        
        assert "Agents:" in result.output
        assert "Pending Approvals:" in result.output
        assert "Cost Today:" in result.output


class TestCLIList:
    """Test list command"""
    
    def test_list_command(self):
        """Test list command shows pending approvals"""
        result = runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "Pending Approvals" in result.output
    
    def test_list_shows_approvals(self):
        """List should show approval details"""
        result = runner.invoke(app, ["list"])
        
        assert "apr-001" in result.output
        assert "claude-code" in result.output  # truncated but visible
    
    def test_list_shows_danger_levels(self):
        """List should show colored danger levels"""
        result = runner.invoke(app, ["list"])
        
        assert "HIGH" in result.output or "🔴" in result.output
        assert "CRITICAL" in result.output or "🚨" in result.output


class TestCLIApprove:
    """Test approve command"""
    
    def test_approve_command(self):
        """Test approve command"""
        result = runner.invoke(app, ["approve", "apr-001", "--force"])
        
        assert result.exit_code == 0
        assert "Approved" in result.output
        assert "apr-001" in result.output
    
    def test_approve_with_scope(self):
        """Test approve with different scopes"""
        for scope in ["once", "session", "workspace", "always"]:
            result = runner.invoke(app, ["approve", "apr-001", "--scope", scope, "--force"])
            
            assert result.exit_code == 0
            assert scope in result.output
    
    def test_approve_invalid_scope(self):
        """Test approve with invalid scope"""
        result = runner.invoke(app, ["approve", "apr-001", "--scope", "invalid", "--force"])
        
        assert result.exit_code != 0
        assert "Invalid scope" in result.output
    
    def test_approve_confirmation_prompt(self):
        """Test approve without --force prompts for confirmation"""
        result = runner.invoke(app, ["approve", "apr-001"], input="y\n")
        
        assert result.exit_code == 0
        assert "Approve" in result.output


class TestCLIReject:
    """Test reject command"""
    
    def test_reject_command(self):
        """Test reject command"""
        result = runner.invoke(app, ["reject", "apr-001", "--force"])
        
        assert result.exit_code == 0
        assert "Rejected" in result.output
        assert "apr-001" in result.output
    
    def test_reject_with_comments(self):
        """Test reject with comments"""
        result = runner.invoke(app, ["reject", "apr-001", "--comments", "Too risky", "--force"])
        
        assert result.exit_code == 0
        assert "Too risky" in result.output


class TestCLIAgents:
    """Test agents command"""
    
    def test_agents_command(self):
        """Test agents command"""
        result = runner.invoke(app, ["agents"])
        
        assert result.exit_code == 0
        assert "Active Agents" in result.output
        assert "claude-code-prod" in result.output
    
    def test_agents_shows_status(self):
        """Agents should show status with emojis"""
        result = runner.invoke(app, ["agents"])
        
        assert result.exit_code == 0
        assert "running" in result.output or "🟢" in result.output


class TestCLICosts:
    """Test costs command"""
    
    def test_costs_command(self):
        """Test costs command"""
        result = runner.invoke(app, ["costs"])
        
        assert result.exit_code == 0
        assert "Cost Summary" in result.output
        assert "$47.83" in result.output
    
    def test_costs_with_breakdown(self):
        """Test costs with breakdown"""
        result = runner.invoke(app, ["costs", "--breakdown"])
        
        assert result.exit_code == 0
        assert "By Agent" in result.output
        assert "By Provider" in result.output
    
    def test_costs_shows_budget_bar(self):
        """Costs should show visual budget bar"""
        result = runner.invoke(app, ["costs"])
        
        assert result.exit_code == 0
        assert "█" in result.output  # Progress bar


class TestCLIConfig:
    """Test config command"""
    
    def test_config_command(self):
        """Test config command shows config"""
        result = runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        assert "FleetOps Config" in result.output
    
    def test_config_shows_api_url(self):
        """Config should show API URL"""
        result = runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        assert "API URL:" in result.output


class TestCLIHelp:
    """Test help output"""
    
    def test_main_help(self):
        """Test main help message"""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "FleetOps CLI" in result.output
    
    def test_command_help(self):
        """Test individual command help"""
        commands = ["status", "list", "approve", "reject", "agents", "costs", "config"]
        
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.output


class TestCLIColors:
    """Test colored output"""
    
    def test_danger_colors(self):
        """Different danger levels should have different colors"""
        result = runner.invoke(app, ["list"])
        
        # Should contain ANSI color codes or emoji
        assert result.exit_code == 0
        assert any(emoji in result.output for emoji in ["🔴", "🚨", "🟠", "🟢", "🟡"])
