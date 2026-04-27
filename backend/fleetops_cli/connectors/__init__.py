"""FleetOps Universal Connector System

Connect any CLI, agent, or IDE to FleetOps with zero code changes.

Pre-built connectors:
- Codex CLI
- Copilot CLI
- OpenCode CLI
- Heroku CLI
- OpenClaw CLI
- Any custom CLI via manifest

Usage:
    from fleetops_cli.connectors import ConnectorRegistry
    
    # Use pre-built connector
    registry = ConnectorRegistry()
    codex = registry.get("codex")
    codex.wrap_cli()
    
    # Create custom connector
    custom = registry.create_from_manifest("my-tool.json")
    custom.wrap_cli()
"""

from .base import BaseConnector, ConnectorManifest
from .registry import ConnectorRegistry
from .codex import CodexConnector
from .copilot import CopilotConnector
from .opencode import OpenCodeConnector
from .heroku import HerokuConnector
from .openclaw import OpenClawConnector
from .generic import GenericCLIConnector

__all__ = [
    "BaseConnector",
    "ConnectorManifest",
    "ConnectorRegistry",
    "CodexConnector",
    "CopilotConnector",
    "OpenCodeConnector",
    "HerokuConnector",
    "OpenClawConnector",
    "GenericCLIConnector",
]
