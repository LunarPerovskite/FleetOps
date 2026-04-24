"""Unit tests for FleetOps CLI."""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add CLI to path
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/cli')
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

# Import using importlib
import importlib.util
cli_path = '/data/.openclaw/workspace/fleetops-temp/cli/fleetops'
spec = importlib.util.spec_from_file_location("fleetops_cli", cli_path)
fleetops_module = importlib.util.module_from_spec(spec)
sys.modules["fleetops_cli"] = fleetops_module
spec.loader.exec_module(fleetops_module)

print_header = fleetops_module.print_header
print_table = fleetops_module.print_table
cmd_status = fleetops_module.cmd_status
cmd_config = fleetops_module.cmd_config
main = fleetops_module.main


class TestPrintHelpers:
    """Test print helper functions."""

    def test_print_header(self, capsys):
        """Test header printing."""
        print_header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out
        assert "=" in captured.out

    def test_print_table(self, capsys):
        """Test table printing."""
        headers = ["Name", "Status"]
        rows = [["Agent1", "Active"], ["Agent2", "Idle"]]
        print_table(headers, rows)
        captured = capsys.readouterr()
        assert "Name" in captured.out
        assert "Agent1" in captured.out
        assert "Active" in captured.out


class TestCLICommands:
    """Test CLI commands."""

    def test_status_command(self, capsys):
        """Test status command."""
        args = MagicMock()
        cmd_status(args)
        captured = capsys.readouterr()
        assert "FleetOps" in captured.out
        assert "0.1.0" in captured.out

    def test_config_command(self, capsys):
        """Test config command."""
        args = MagicMock()
        cmd_config(args)
        captured = capsys.readouterr()
        assert "FleetOps Configuration" in captured.out
        assert "***REDACTED***" in captured.out or "NOT SET" in captured.out


class TestCLIArguments:
    """Test CLI argument parsing."""

    @patch("fleetops.cmd_status")
    def test_status_subcommand(self, mock_status):
        """Test status subcommand."""
        with patch.object(sys, "argv", ["fleetops", "status"]):
            try:
                main()
            except SystemExit:
                pass
        mock_status.assert_called_once()

    @patch("fleetops.cmd_config")
    def test_config_subcommand(self, mock_config):
        """Test config subcommand."""
        with patch.object(sys, "argv", ["fleetops", "config"]):
            try:
                main()
            except SystemExit:
                pass
        mock_config.assert_called_once()

    def test_no_command(self, capsys):
        """Test no command prints help."""
        with patch.object(sys, "argv", ["fleetops"]):
            try:
                main()
            except SystemExit:
                pass
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()
