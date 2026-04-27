"""FleetOps CLI — Universal Agent Governance Tool

A CLI tool and Python library for managing AI agent approvals, costs, and governance.
Works with any agent: Claude Code, Roo Code, Copilot, VS Code extensions, Cursor, etc.

Usage as CLI:
    fleetops status
    fleetops approve <id> --scope session
    fleetops reject <id>

Usage as library:
    from fleetops_cli import FleetOpsClient
    client = FleetOpsClient(api_url="http://localhost:8000")
    client.approve("approval-123", scope="session")

Usage as VS Code/Cursor extension:
    See fleetops_cli.ide module for IDE integration helpers.
"""

__version__ = "0.1.0"
__author__ = "FleetOps Team"
__license__ = "MIT"

from .client import FleetOpsClient
from .ide import FleetOpsIDEExtension

__all__ = ["FleetOpsClient", "FleetOpsIDEExtension"]
