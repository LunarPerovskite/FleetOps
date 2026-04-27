"""OpenClaw CLI Connector for FleetOps

Wraps OpenClaw CLI with governance.
"""

from .base import BaseConnector, ConnectorManifest


class OpenClawConnector(BaseConnector):
    """Connector for OpenClaw CLI"""

    def __init__(self):
        manifest = ConnectorManifest(
            name="openclaw",
            cli_command="openclaw",
            version="1.0.0",
            description="OpenClaw CLI connector",
            intercept_patterns=["openclaw", "claw"],
            danger_rules=[
                {"pattern": r"deploy|publish|release", "level": "high"},
                {"pattern": r"gateway stop|gateway restart", "level": "critical"},
                {"pattern": r"config set|config patch", "level": "medium"},
                {"pattern": r"status|list|help", "level": "safe"},
            ],
            auto_approve_safe=True
        )
        super().__init__(manifest)

    @property
    def name(self) -> str:
        return "openclaw"

    @property
    def cli_command(self) -> str:
        return "openclaw"

    def _analyze_danger(self, command: str, args: tuple) -> str:
        """OpenClaw-specific danger analysis"""
        full = f"{command} {' '.join(args)}".lower()

        if "gateway stop" in full or "gateway restart" in full:
            return "critical"

        if "deploy" in full or "publish" in full:
            return "high"

        if "config" in full and ("set" in full or "patch" in full):
            return "medium"

        return "safe"
