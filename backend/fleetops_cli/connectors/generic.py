"""Generic CLI Connector for FleetOps

Allows users to create connectors for ANY CLI tool via JSON manifest.

Usage:
    # Create a manifest file my-tool.json:
    {
        "name": "my-custom-tool",
        "cli_command": "mytool",
        "version": "1.0.0",
        "description": "My custom CLI tool",
        "intercept_patterns": ["mytool"],
        "danger_rules": [
            {"pattern": "delete", "level": "high"},
            {"pattern": "create", "level": "low"}
        ],
        "auto_approve_safe": true
    }
    
    # Use it:
    from fleetops_cli.connectors import GenericCLIConnector
    
    connector = GenericCLIConnector.from_manifest("my-tool.json")
    connector.wrap_cli()
"""

import json
import os
from .base import BaseConnector, ConnectorManifest


class GenericCLIConnector(BaseConnector):
    """Generic connector that can wrap any CLI tool"""
    
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)
        self._manifest_data = manifest
    
    @property
    def name(self) -> str:
        return self._manifest_data.name
    
    @property
    def cli_command(self) -> str:
        return self._manifest_data.cli_command
    
    @classmethod
    def from_manifest(cls, manifest_path: str) -> "GenericCLIConnector":
        """Create connector from JSON manifest file"""
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        manifest = ConnectorManifest(
            name=data["name"],
            cli_command=data["cli_command"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            intercept_patterns=data.get("intercept_patterns", []),
            danger_rules=data.get("danger_rules", []),
            auto_approve_safe=data.get("auto_approve_safe", True)
        )
        
        return cls(manifest)
    
    @classmethod
    def from_dict(cls, data: dict) -> "GenericCLIConnector":
        """Create connector from dictionary"""
        manifest = ConnectorManifest(
            name=data["name"],
            cli_command=data["cli_command"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            intercept_patterns=data.get("intercept_patterns", []),
            danger_rules=data.get("danger_rules", []),
            auto_approve_safe=data.get("auto_approve_safe", True)
        )
        
        return cls(manifest)
    
    def to_dict(self) -> dict:
        """Export connector manifest as dictionary"""
        return {
            "name": self.manifest.name,
            "cli_command": self.manifest.cli_command,
            "version": self.manifest.version,
            "description": self.manifest.description,
            "author": self.manifest.author,
            "intercept_patterns": self.manifest.intercept_patterns,
            "danger_rules": self.manifest.danger_rules,
            "auto_approve_safe": self.manifest.auto_approve_safe
        }
    
    def save_manifest(self, path: str) -> None:
        """Save connector manifest to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Pre-built connector manifests for popular tools
PREBUILT_MANIFESTS = {
    "docker": {
        "name": "docker",
        "cli_command": "docker",
        "version": "1.0.0",
        "description": "Docker CLI connector",
        "intercept_patterns": ["docker"],
        "danger_rules": [
            {"pattern": r"rm.*-f|system prune", "level": "critical"},
            {"pattern": r"push|publish", "level": "high"},
            {"pattern": r"run.*-v|run.*--privileged", "level": "medium"},
            {"pattern": r"ps|logs|images", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "kubectl": {
        "name": "kubectl",
        "cli_command": "kubectl",
        "version": "1.0.0",
        "description": "Kubernetes CLI connector",
        "intercept_patterns": ["kubectl", "k"],
        "danger_rules": [
            {"pattern": r"delete|drain|cordon", "level": "critical"},
            {"pattern": r"apply|patch|scale", "level": "high"},
            {"pattern": r"exec|logs|describe", "level": "medium"},
            {"pattern": r"get|top", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "aws": {
        "name": "aws",
        "cli_command": "aws",
        "version": "1.0.0",
        "description": "AWS CLI connector",
        "intercept_patterns": ["aws"],
        "danger_rules": [
            {"pattern": r"delete|terminate|destroy", "level": "critical"},
            {"pattern": r"create|update|put", "level": "high"},
            {"pattern": r"stop|deregister", "level": "medium"},
            {"pattern": r"describe|list|get", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "gcloud": {
        "name": "gcloud",
        "cli_command": "gcloud",
        "version": "1.0.0",
        "description": "Google Cloud CLI connector",
        "intercept_patterns": ["gcloud"],
        "danger_rules": [
            {"pattern": r"delete|destroy|remove", "level": "critical"},
            {"pattern": r"create|deploy|update", "level": "high"},
            {"pattern": r"stop|disable", "level": "medium"},
            {"pattern": r"list|describe|info", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "terraform": {
        "name": "terraform",
        "cli_command": "terraform",
        "version": "1.0.0",
        "description": "Terraform CLI connector",
        "intercept_patterns": ["terraform", "tf"],
        "danger_rules": [
            {"pattern": r"destroy", "level": "critical"},
            {"pattern": r"apply|import", "level": "high"},
            {"pattern": r"plan", "level": "medium"},
            {"pattern": r"show|output|state list", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "npm": {
        "name": "npm",
        "cli_command": "npm",
        "version": "1.0.0",
        "description": "NPM CLI connector",
        "intercept_patterns": ["npm"],
        "danger_rules": [
            {"pattern": r"publish|unpublish", "level": "high"},
            {"pattern": r"install|uninstall", "level": "low"},
            {"pattern": r"audit fix", "level": "medium"},
            {"pattern": r"list|info|search", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "pip": {
        "name": "pip",
        "cli_command": "pip",
        "version": "1.0.0",
        "description": "Pip CLI connector",
        "intercept_patterns": ["pip"],
        "danger_rules": [
            {"pattern": r"install.*--user|uninstall", "level": "low"},
            {"pattern": r"install|download", "level": "safe"},
            {"pattern": r"list|show|freeze", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "git": {
        "name": "git",
        "cli_command": "git",
        "version": "1.0.0",
        "description": "Git CLI connector",
        "intercept_patterns": ["git"],
        "danger_rules": [
            {"pattern": r"push.*-f|push.*--force", "level": "critical"},
            {"pattern": r"reset.*--hard|clean.*-f", "level": "high"},
            {"pattern": r"push|merge|rebase", "level": "medium"},
            {"pattern": r"status|log|diff", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "fly": {
        "name": "fly",
        "cli_command": "fly",
        "version": "1.0.0",
        "description": "Fly.io CLI connector",
        "intercept_patterns": ["fly"],
        "danger_rules": [
            {"pattern": r"apps destroy|machines destroy", "level": "critical"},
            {"pattern": r"deploy|scale", "level": "high"},
            {"pattern": r"secrets set|secrets unset", "level": "medium"},
            {"pattern": r"status|logs|info", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "vercel": {
        "name": "vercel",
        "cli_command": "vercel",
        "version": "1.0.0",
        "description": "Vercel CLI connector",
        "intercept_patterns": ["vercel", "vc"],
        "danger_rules": [
            {"pattern": r"remove|delete", "level": "critical"},
            {"pattern": r"deploy|promote", "level": "high"},
            {"pattern": r"env add|env rm", "level": "medium"},
            {"pattern": r"list|info|logs", "level": "safe"}
        ],
        "auto_approve_safe": True
    }
}


def get_prebuilt_manifest(name: str) -> dict:
    """Get a pre-built connector manifest by name"""
    return PREBUILT_MANIFESTS.get(name, {})


def list_prebuilt_connectors() -> list:
    """List all available pre-built connectors"""
    return list(PREBUILT_MANIFESTS.keys())
