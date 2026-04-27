"""Codex CLI Connector for FleetOps

Wraps OpenAI's Codex CLI with governance.

Usage:
    from fleetops_cli.connectors import CodexConnector
    
    connector = CodexConnector()
    connector.wrap_cli()  # Now `codex` routes through FleetOps
"""

from .base import BaseConnector, ConnectorManifest


class CodexConnector(BaseConnector):
    """Connector for OpenAI Codex CLI"""
    
    def __init__(self):
        manifest = ConnectorManifest(
            name="codex",
            cli_command="codex",
            version="1.0.0",
            description="OpenAI Codex CLI connector",
            intercept_patterns=["codex", "npx codex"],
            danger_rules=[
                {"pattern": r"--auto-approve|approve-all", "level": "high"},
                {"pattern": r"rm\s+-rf|delete|remove", "level": "critical"},
                {"pattern": r"deploy|push|publish", "level": "medium"},
                {"pattern": r"install|npm i|pip install", "level": "low"},
            ],
            auto_approve_safe=True
        )
        super().__init__(manifest)
    
    @property
    def name(self) -> str:
        return "codex"
    
    @property
    def cli_command(self) -> str:
        return "codex"
    
    def _analyze_danger(self, command: str, args: tuple) -> str:
        """Codex-specific danger analysis"""
        full = f"{command} {' '.join(args)}".lower()
        
        # Check for dangerous patterns
        if "--auto-approve" in full or "--no-confirm" in full:
            return "critical"  # Bypassing safety is always critical
        
        if "rm -rf" in full or "delete" in full:
            return "high"
        
        if "deploy" in full or "push" in full:
            return "medium"
        
        return "safe"
