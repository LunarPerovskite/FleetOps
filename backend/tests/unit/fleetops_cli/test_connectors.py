"""Tests for FleetOps Connectors"""
import pytest
import sys
import json
import os
from unittest.mock import patch

# sys.path removed - using PYTHONPATH

from fleetops_cli.connectors import (
    ConnectorRegistry,
    CodexConnector,
    CopilotConnector,
    HerokuConnector,
    GenericCLIConnector
)
from fleetops_cli.connectors.generic import PREBUILT_MANIFESTS, list_prebuilt_connectors


class TestConnectorRegistry:
    """Test connector registry"""
    
    def test_create_registry(self):
        """Test creating registry"""
        registry = ConnectorRegistry()
        assert registry is not None
        
        # Should have pre-built connectors
        connectors = registry.list()
        assert len(connectors) > 0
    
    def test_get_codex(self):
        """Test getting Codex connector"""
        registry = ConnectorRegistry()
        codex = registry.get("codex")
        
        assert codex is not None
        assert codex.name == "codex"
    
    def test_get_copilot(self):
        """Test getting Copilot connector"""
        registry = ConnectorRegistry()
        copilot = registry.get("copilot")
        
        assert copilot is not None
        assert copilot.name == "copilot"
    
    def test_get_heroku(self):
        """Test getting Heroku connector"""
        registry = ConnectorRegistry()
        heroku = registry.get("heroku")
        
        assert heroku is not None
        assert heroku.name == "heroku"
    
    def test_get_nonexistent(self):
        """Test getting non-existent connector"""
        registry = ConnectorRegistry()
        result = registry.get("nonexistent")
        
        assert result is None
    
    def test_create_from_prebuilt(self):
        """Test creating from pre-built manifest"""
        registry = ConnectorRegistry()
        
        # Test docker connector
        docker = registry.create_from_prebuilt("docker")
        assert docker is not None
        assert docker.name == "docker"
    
    def test_list_prebuilt(self):
        """Test listing pre-built connectors"""
        names = list_prebuilt_connectors()
        
        assert len(names) > 0
        assert "docker" in names
        assert "kubectl" in names
        assert "git" in names


class TestCodexConnector:
    """Test Codex connector"""
    
    def test_codex_properties(self):
        """Test Codex connector properties"""
        codex = CodexConnector()
        
        assert codex.name == "codex"
        assert codex.cli_command == "codex"
    
    def test_codex_danger_analysis(self):
        """Test Codex danger analysis"""
        codex = CodexConnector()
        
        # Auto-approve should be critical
        result = codex._analyze_danger("codex", ("--auto-approve",))
        assert result == "critical"
        
        # Normal command should be safe
        result = codex._analyze_danger("codex", ("hello",))
        assert result == "safe"


class TestCopilotConnector:
    """Test Copilot connector"""
    
    def test_copilot_properties(self):
        """Test Copilot connector properties"""
        copilot = CopilotConnector()
        
        assert copilot.name == "copilot"


class TestHerokuConnector:
    """Test Heroku connector"""
    
    def test_heroku_danger(self):
        """Test Heroku danger analysis"""
        heroku = HerokuConnector()
        
        # Destroy should be critical
        result = heroku._analyze_danger("heroku", ("apps:destroy",))
        assert result == "critical"
        
        # Logs should be safe
        result = heroku._analyze_danger("heroku", ("logs",))
        assert result == "safe"


class TestGenericConnector:
    """Test generic connector"""
    
    def test_create_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "name": "test-tool",
            "cli_command": "testtool",
            "version": "1.0.0",
            "description": "Test tool",
            "intercept_patterns": ["test"],
            "danger_rules": [
                {"pattern": "delete", "level": "high"}
            ]
        }
        
        connector = GenericCLIConnector.from_dict(data)
        
        assert connector.name == "test-tool"
        assert connector.cli_command == "testtool"
    
    def test_export_manifest(self):
        """Test exporting manifest"""
        data = {
            "name": "test-tool",
            "cli_command": "testtool",
            "version": "1.0.0",
        }
        
        connector = GenericCLIConnector.from_dict(data)
        manifest = connector.to_dict()
        
        assert manifest["name"] == "test-tool"
        assert manifest["cli_command"] == "testtool"
    
    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading manifest"""
        data = {
            "name": "my-cli",
            "cli_command": "mycli",
            "version": "1.0.0",
            "danger_rules": [
                {"pattern": "rm", "level": "high"}
            ]
        }
        
        connector = GenericCLIConnector.from_dict(data)
        
        # Save
        manifest_path = tmp_path / "test-manifest.json"
        connector.save_manifest(str(manifest_path))
        
        assert manifest_path.exists()
        
        # Load
        loaded = GenericCLIConnector.from_manifest(str(manifest_path))
        assert loaded.name == "my-cli"


class TestPrebuiltManifests:
    """Test pre-built manifests"""
    
    def test_docker_manifest(self):
        """Test Docker manifest exists"""
        manifest = PREBUILT_MANIFESTS.get("docker")
        assert manifest is not None
        assert manifest["cli_command"] == "docker"
    
    def test_kubectl_manifest(self):
        """Test kubectl manifest exists"""
        manifest = PREBUILT_MANIFESTS.get("kubectl")
        assert manifest is not None
        assert "delete" in str(manifest["danger_rules"])
    
    def test_terraform_manifest(self):
        """Test Terraform manifest"""
        manifest = PREBUILT_MANIFESTS.get("terraform")
        assert manifest is not None
        assert manifest["cli_command"] == "terraform"
    
    def test_git_manifest(self):
        """Test Git manifest"""
        manifest = PREBUILT_MANIFESTS.get("git")
        assert manifest is not None
        # Should detect force push
        assert any("force" in str(rule) for rule in manifest["danger_rules"])


class TestShellIntegration:
    """Test shell integration"""
    
    def test_shell_hook_creation(self, tmp_path):
        """Test shell hook creation"""
        from fleetops_cli.connectors.base import ShellIntegrationConnector
        
        shell = ShellIntegrationConnector()
        
        # Create bash hook
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            shell.install_shell_hook("bash")
            
            hook_path = os.path.join(tmp_path, ".fleetops", "hooks", "bash-hook.sh")
            assert os.path.exists(hook_path)
