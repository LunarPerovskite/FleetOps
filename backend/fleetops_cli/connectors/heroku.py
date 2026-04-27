"""Heroku CLI Connector for FleetOps

Wraps Heroku CLI with governance.
"""

from .base import BaseConnector, ConnectorManifest


class HerokuConnector(BaseConnector):
    """Connector for Heroku CLI"""

    def __init__(self):
        manifest = ConnectorManifest(
            name="heroku",
            cli_command="heroku",
            version="1.0.0",
            description="Heroku CLI connector",
            intercept_patterns=["heroku"],
            danger_rules=[
                {"pattern": r"apps:destroy|delete", "level": "critical"},
                {"pattern": r"config:set|config:unset", "level": "high"},
                {"pattern": r"ps:restart|ps:stop", "level": "medium"},
                {"pattern": r"logs|info", "level": "safe"},
            ],
            auto_approve_safe=True
        )
        super().__init__(manifest)

    @property
    def name(self) -> str:
        return "heroku"

    @property
    def cli_command(self) -> str:
        return "heroku"

    def _analyze_danger(self, command: str, args: tuple) -> str:
        """Heroku-specific danger analysis"""
        full = f"{command} {' '.join(args)}".lower()

        if "apps:destroy" in full or "apps:delete" in full:
            return "critical"

        if "config:set" in full or "config:unset" in full:
            return "high"

        if "ps:restart" in full or "ps:stop" in full:
            return "medium"

        return "safe"
