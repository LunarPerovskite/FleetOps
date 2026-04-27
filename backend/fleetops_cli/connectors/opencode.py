"""OpenCode CLI Connector for FleetOps

Wraps OpenCode CLI with governance.
"""

from .base import BaseConnector, ConnectorManifest


class OpenCodeConnector(BaseConnector):
    """Connector for OpenCode CLI"""

    def __init__(self):
        manifest = ConnectorManifest(
            name="opencode",
            cli_command="opencode",
            version="1.0.0",
            description="OpenCode CLI connector",
            intercept_patterns=["opencode"],
            danger_rules=[
                {"pattern": r"execute|run", "level": "medium"},
                {"pattern": r"deploy|publish", "level": "high"},
                {"pattern": r"rm|delete", "level": "critical"},
            ],
            auto_approve_safe=True
        )
        super().__init__(manifest)

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def cli_command(self) -> str:
        return "opencode"
