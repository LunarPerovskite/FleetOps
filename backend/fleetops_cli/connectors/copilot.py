"""Copilot CLI Connector for FleetOps

Wraps GitHub Copilot CLI with governance.
"""

from .base import BaseConnector, ConnectorManifest


class CopilotConnector(BaseConnector):
    """Connector for GitHub Copilot CLI"""
    
    def __init__(self):
        manifest = ConnectorManifest(
            name="copilot",
            cli_command="gh copilot",
            version="1.0.0",
            description="GitHub Copilot CLI connector",
            intercept_patterns=["gh copilot", "copilot"],
            danger_rules=[
                {"pattern": r"suggest|explain", "level": "safe"},
                {"pattern": r"execute|run", "level": "medium"},
                {"pattern": r"deploy|push|merge", "level": "high"},
            ],
            auto_approve_safe=True
        )
        super().__init__(manifest)
    
    @property
    def name(self) -> str:
        return "copilot"
    
    @property
    def cli_command(self) -> str:
        return "gh"
    
    def _analyze_danger(self, command: str, args: tuple) -> str:
        """Copilot-specific danger analysis"""
        full = f"{command} {' '.join(args)}".lower()
        
        if "execute" in full or "run" in full:
            return "medium"
        
        if "deploy" in full or "push" in full:
            return "high"
        
        return "safe"
