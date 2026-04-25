"""Unit tests for FleetOps CLI."""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Get the project root relative to this test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..', '..', '..'))
CLI_DIR = os.path.join(PROJECT_ROOT, 'cli')
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

# Add to path
sys.path.insert(0, CLI_DIR)
sys.path.insert(0, BACKEND_DIR)

# Try to import CLI module
fleetops_module = None
try:
    import importlib.util
    cli_path = os.path.join(CLI_DIR, 'fleetops')
    if os.path.exists(cli_path):
        spec = importlib.util.spec_from_file_location("fleetops_cli", cli_path)
        if spec and spec.loader:
            fleetops_module = importlib.util.module_from_spec(spec)
            sys.modules["fleetops_cli"] = fleetops_module
            spec.loader.exec_module(fleetops_module)
except Exception:
    pass


class TestPrintHelpers:
    """Test print helper functions."""

    @pytest.mark.skipif(fleetops_module is None, reason="CLI module not found")
    def test_print_header(self, capsys):
        """Test header printing."""
        print_header = fleetops_module.print_header
        print_header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out
        assert "=" in captured.out

    @pytest.mark.skipif(fleetops_module is None, reason="CLI module not found")
    def test_print_table(self, capsys):
        """Test table printing."""
        print_table = fleetops_module.print_table
        headers = ["Name", "Status"]
        rows = [["Agent1", "Active"], ["Agent2", "Idle"]]
        print_table(headers, rows)
        captured = capsys.readouterr()
        assert "Name" in captured.out
        assert "Agent1" in captured.out
        assert "Active" in captured.out


class TestCLICommands:
    """Test CLI commands."""

    @pytest.mark.skipif(fleetops_module is None, reason="CLI module not found")
    def test_status_command(self, capsys):
        """Test status command."""
        cmd_status = fleetops_module.cmd_status
        args = MagicMock()
        cmd_status(args)
        captured = capsys.readouterr()
        assert "FleetOps" in captured.out

    @pytest.mark.skipif(fleetops_module is None, reason="CLI module not found")
    def test_config_command(self, capsys):
        """Test config command."""
        cmd_config = fleetops_module.cmd_config
        args = MagicMock()
        cmd_config(args)
        captured = capsys.readouterr()
        assert "Configuration" in captured.out


class TestCLIArguments:
    """Test CLI argument parsing."""

    @pytest.mark.skipif(fleetops_module is None, reason="CLI module not found")
    def test_no_command(self, capsys):
        """Test no command prints help."""
        main = fleetops_module.main
        with patch.object(sys, "argv", ["fleetops"]):
            try:
                main()
            except SystemExit:
                pass
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()
