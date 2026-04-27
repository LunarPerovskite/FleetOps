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
    },
    # ─── DATABASE TOOLS ───
    "psql": {
        "name": "psql",
        "cli_command": "psql",
        "version": "1.0.0",
        "description": "PostgreSQL CLI connector",
        "intercept_patterns": ["psql"],
        "danger_rules": [
            {"pattern": r"DELETE|DROP|TRUNCATE", "level": "critical"},
            {"pattern": r"UPDATE|INSERT|ALTER", "level": "high"},
            {"pattern": r"SELECT", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "mysql": {
        "name": "mysql",
        "cli_command": "mysql",
        "version": "1.0.0",
        "description": "MySQL CLI connector",
        "intercept_patterns": ["mysql"],
        "danger_rules": [
            {"pattern": r"DELETE|DROP|TRUNCATE", "level": "critical"},
            {"pattern": r"UPDATE|INSERT|ALTER", "level": "high"},
            {"pattern": r"SELECT|SHOW|DESCRIBE", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "mongosh": {
        "name": "mongosh",
        "cli_command": "mongosh",
        "version": "1.0.0",
        "description": "MongoDB Shell connector",
        "intercept_patterns": ["mongosh", "mongo"],
        "danger_rules": [
            {"pattern": r"db\.drop|deleteMany|dropDatabase", "level": "critical"},
            {"pattern": r"insert|update|remove", "level": "high"},
            {"pattern": r"find|aggregate", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "redis-cli": {
        "name": "redis-cli",
        "cli_command": "redis-cli",
        "version": "1.0.0",
        "description": "Redis CLI connector",
        "intercept_patterns": ["redis-cli"],
        "danger_rules": [
            {"pattern": r"FLUSHALL|FLUSHDB|DEL", "level": "critical"},
            {"pattern": r"SET|HSET|LPUSH", "level": "medium"},
            {"pattern": r"GET|HGET|LRANGE", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── CLOUD PROVIDERS ───
    "azure": {
        "name": "azure",
        "cli_command": "az",
        "version": "1.0.0",
        "description": "Azure CLI connector",
        "intercept_patterns": ["az"],
        "danger_rules": [
            {"pattern": r"delete|purge|uninstall", "level": "critical"},
            {"pattern": r"create|deploy|update", "level": "high"},
            {"pattern": r"stop|deallocate", "level": "medium"},
            {"pattern": r"list|show|get", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "digitalocean": {
        "name": "digitalocean",
        "cli_command": "doctl",
        "version": "1.0.0",
        "description": "DigitalOcean CLI connector",
        "intercept_patterns": ["doctl"],
        "danger_rules": [
            {"pattern": r"delete|destroy", "level": "critical"},
            {"pattern": r"create|update", "level": "high"},
            {"pattern": r"get|list", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "linode": {
        "name": "linode",
        "cli_command": "linode-cli",
        "version": "1.0.0",
        "description": "Linode CLI connector",
        "intercept_patterns": ["linode-cli"],
        "danger_rules": [
            {"pattern": r"delete|shutdown", "level": "critical"},
            {"pattern": r"create|update", "level": "high"},
            {"pattern": r"list|view", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── CI/CD TOOLS ───
    "github-actions": {
        "name": "github-actions",
        "cli_command": "gh",
        "version": "1.0.0",
        "description": "GitHub Actions CLI connector",
        "intercept_patterns": ["gh workflow"],
        "danger_rules": [
            {"pattern": r"delete|disable", "level": "critical"},
            {"pattern": r"run|trigger", "level": "medium"},
            {"pattern": r"list|view|status", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "circleci": {
        "name": "circleci",
        "cli_command": "circleci",
        "version": "1.0.0",
        "description": "CircleCI CLI connector",
        "intercept_patterns": ["circleci"],
        "danger_rules": [
            {"pattern": r"delete|unfollow", "level": "critical"},
            {"pattern": r"setup|deploy", "level": "medium"},
            {"pattern": r"config|validate", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── CONTAINER TOOLS ───
    "helm": {
        "name": "helm",
        "cli_command": "helm",
        "version": "1.0.0",
        "description": "Helm CLI connector",
        "intercept_patterns": ["helm"],
        "danger_rules": [
            {"pattern": r"delete|uninstall|purge", "level": "critical"},
            {"pattern": r"install|upgrade|rollback", "level": "high"},
            {"pattern": r"list|status|history", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "podman": {
        "name": "podman",
        "cli_command": "podman",
        "version": "1.0.0",
        "description": "Podman CLI connector",
        "intercept_patterns": ["podman"],
        "danger_rules": [
            {"pattern": r"rm.*-f|system prune", "level": "critical"},
            {"pattern": r"push|publish", "level": "high"},
            {"pattern": r"run.*-v|run.*--privileged", "level": "medium"},
            {"pattern": r"ps|logs|images", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── MONITORING ───
    "datadog": {
        "name": "datadog",
        "cli_command": "datadog-ci",
        "version": "1.0.0",
        "description": "Datadog CLI connector",
        "intercept_patterns": ["datadog-ci"],
        "danger_rules": [
            {"pattern": r"delete|remove", "level": "critical"},
            {"pattern": r"upload|synthetics", "level": "medium"},
            {"pattern": r"tag|metric", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "sentry": {
        "name": "sentry",
        "cli_command": "sentry-cli",
        "version": "1.0.0",
        "description": "Sentry CLI connector",
        "intercept_patterns": ["sentry-cli"],
        "danger_rules": [
            {"pattern": r"delete|remove", "level": "critical"},
            {"pattern": r"deploy|release", "level": "high"},
            {"pattern": r"upload-sourcemaps", "level": "medium"},
            {"pattern": r"info|list", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── VERSION MANAGERS ───
    "nvm": {
        "name": "nvm",
        "cli_command": "nvm",
        "version": "1.0.0",
        "description": "NVM connector",
        "intercept_patterns": ["nvm"],
        "danger_rules": [
            {"pattern": r"uninstall|reinstall", "level": "low"},
            {"pattern": r"install|use", "level": "safe"},
            {"pattern": r"list|current", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "pyenv": {
        "name": "pyenv",
        "cli_command": "pyenv",
        "version": "1.0.0",
        "description": "Pyenv connector",
        "intercept_patterns": ["pyenv"],
        "danger_rules": [
            {"pattern": r"uninstall|rehash", "level": "low"},
            {"pattern": r"install|global|local", "level": "safe"},
            {"pattern": r"versions|which", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "rbenv": {
        "name": "rbenv",
        "cli_command": "rbenv",
        "version": "1.0.0",
        "description": "Rbenv connector",
        "intercept_patterns": ["rbenv"],
        "danger_rules": [
            {"pattern": r"uninstall", "level": "low"},
            {"pattern": r"install|global|local", "level": "safe"},
            {"pattern": r"versions|which", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── PACKAGE MANAGERS ───
    "homebrew": {
        "name": "homebrew",
        "cli_command": "brew",
        "version": "1.0.0",
        "description": "Homebrew connector",
        "intercept_patterns": ["brew"],
        "danger_rules": [
            {"pattern": r"uninstall|remove|cleanup", "level": "low"},
            {"pattern": r"install|upgrade|tap", "level": "safe"},
            {"pattern": r"list|search|info", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "apt": {
        "name": "apt",
        "cli_command": "apt",
        "version": "1.0.0",
        "description": "APT connector",
        "intercept_patterns": ["apt", "apt-get"],
        "danger_rules": [
            {"pattern": r"remove|purge|autoremove", "level": "medium"},
            {"pattern": r"install|update|upgrade", "level": "low"},
            {"pattern": r"list|search|show", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── SECURITY ───
    "openssl": {
        "name": "openssl",
        "cli_command": "openssl",
        "version": "1.0.0",
        "description": "OpenSSL connector",
        "intercept_patterns": ["openssl"],
        "danger_rules": [
            {"pattern": r"delete|remove", "level": "critical"},
            {"pattern": r"genrsa|req|x509", "level": "high"},
            {"pattern": r"verify|s_client", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "gpg": {
        "name": "gpg",
        "cli_command": "gpg",
        "version": "1.0.0",
        "description": "GPG connector",
        "intercept_patterns": ["gpg"],
        "danger_rules": [
            {"pattern": r"delete-secret|delete-key", "level": "critical"},
            {"pattern": r"sign|encrypt|decrypt", "level": "high"},
            {"pattern": r"list|fingerprint", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "ssh": {
        "name": "ssh",
        "cli_command": "ssh",
        "version": "1.0.0",
        "description": "SSH connector",
        "intercept_patterns": ["ssh"],
        "danger_rules": [
            {"pattern": r"rm|dd|mkfs", "level": "critical"},
            {"pattern": r"scp|sftp", "level": "medium"},
            {"pattern": r"ssh.*-L|ssh.*-D", "level": "medium"},
            {"pattern": r"ssh.*hostname", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── TESTING ───
    "jest": {
        "name": "jest",
        "cli_command": "jest",
        "version": "1.0.0",
        "description": "Jest connector",
        "intercept_patterns": ["jest"],
        "danger_rules": [
            {"pattern": r"clearCache", "level": "low"},
            {"pattern": r"watch|run|test", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "pytest": {
        "name": "pytest",
        "cli_command": "pytest",
        "version": "1.0.0",
        "description": "Pytest connector",
        "intercept_patterns": ["pytest"],
        "danger_rules": [
            {"pattern": r"clearcache", "level": "low"},
            {"pattern": r"run|test", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "cypress": {
        "name": "cypress",
        "cli_command": "cypress",
        "version": "1.0.0",
        "description": "Cypress connector",
        "intercept_patterns": ["cypress"],
        "danger_rules": [
            {"pattern": r"run.*--record", "level": "medium"},
            {"pattern": r"open|run", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── MOBILE DEV ───
    "flutter": {
        "name": "flutter",
        "cli_command": "flutter",
        "version": "1.0.0",
        "description": "Flutter connector",
        "intercept_patterns": ["flutter"],
        "danger_rules": [
            {"pattern": r"build.*--release|publish", "level": "high"},
            {"pattern": r"build|run", "level": "low"},
            {"pattern": r"doctor|devices", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "react-native": {
        "name": "react-native",
        "cli_command": "react-native",
        "version": "1.0.0",
        "description": "React Native connector",
        "intercept_patterns": ["react-native"],
        "danger_rules": [
            {"pattern": r"build.*--release|publish", "level": "high"},
            {"pattern": r"build|run|start", "level": "low"},
            {"pattern": r"info|doctor", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── API TOOLS ───
    "curl": {
        "name": "curl",
        "cli_command": "curl",
        "version": "1.0.0",
        "description": "cURL connector",
        "intercept_patterns": ["curl"],
        "danger_rules": [
            {"pattern": r"DELETE|PUT|PATCH", "level": "high"},
            {"pattern": r"POST", "level": "medium"},
            {"pattern": r"GET|HEAD", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "wget": {
        "name": "wget",
        "cli_command": "wget",
        "version": "1.0.0",
        "description": "Wget connector",
        "intercept_patterns": ["wget"],
        "danger_rules": [
            {"pattern": r"--post-data|--method", "level": "medium"},
            {"pattern": r"download", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── COMMUNICATION ───
    "slack-cli": {
        "name": "slack-cli",
        "cli_command": "slack",
        "version": "1.0.0",
        "description": "Slack CLI connector",
        "intercept_patterns": ["slack"],
        "danger_rules": [
            {"pattern": r"admin.*delete|archive", "level": "critical"},
            {"pattern": r"message|post|notify", "level": "low"},
            {"pattern": r"status|list", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── MESSAGE QUEUES ───
    "kafka": {
        "name": "kafka",
        "cli_command": "kafka-topics",
        "version": "1.0.0",
        "description": "Kafka CLI connector",
        "intercept_patterns": ["kafka"],
        "danger_rules": [
            {"pattern": r"delete|alter.*delete", "level": "critical"},
            {"pattern": r"create|alter", "level": "high"},
            {"pattern": r"list|describe", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    "rabbitmq": {
        "name": "rabbitmq",
        "cli_command": "rabbitmqctl",
        "version": "1.0.0",
        "description": "RabbitMQ CLI connector",
        "intercept_patterns": ["rabbitmqctl"],
        "danger_rules": [
            {"pattern": r"delete|purge|clear", "level": "critical"},
            {"pattern": r"add|set|change", "level": "medium"},
            {"pattern": r"list|status", "level": "safe"}
        ],
        "auto_approve_safe": True
    },
    # ─── GAME DEV ───
    "unity": {
        "name": "unity",
        "cli_command": "unity",
        "version": "1.0.0",
        "description": "Unity CLI connector",
        "intercept_patterns": ["unity"],
        "danger_rules": [
            {"pattern": r"build.*-release|publish", "level": "high"},
            {"pattern": r"build|test", "level": "low"},
            {"pattern": r"version|help", "level": "safe"}
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
