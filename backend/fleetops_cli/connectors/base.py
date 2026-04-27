"""Base connector for any CLI tool

Provides the foundation for wrapping any command-line tool with FleetOps governance.
"""

import subprocess
import shlex
import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class ConnectorManifest:
    """Manifest for creating a connector from JSON"""
    name: str
    cli_command: str
    version: str
    intercept_patterns: List[str] = field(default_factory=list)
    danger_rules: List[Dict[str, Any]] = field(default_factory=list)
    auto_approve_safe: bool = True
    description: str = ""
    author: str = ""


class BaseConnector(ABC):
    """Base class for all FleetOps CLI connectors"""
    
    def __init__(self, manifest: Optional[ConnectorManifest] = None):
        self.manifest = manifest
        self._original_cli: Optional[str] = None
        self._wrapped: bool = False
        self._before_hooks: List[Callable] = []
        self._after_hooks: List[Callable] = []
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name"""
        pass
    
    @property
    @abstractmethod
    def cli_command(self) -> str:
        """The CLI command this connector wraps"""
        pass
    
    def wrap_cli(self) -> None:
        """Wrap the CLI command with FleetOps governance
        
        This intercepts the original CLI and routes through FleetOps.
        """
        if self._wrapped:
            print(f"[FleetOps] {self.name} is already wrapped")
            return
        
        # Find the original CLI binary
        self._original_cli = self._find_cli_binary()
        if not self._original_cli:
            print(f"[FleetOps] Warning: {self.cli_command} not found. Skipping wrap.")
            return
        
        # Create wrapper script
        self._create_wrapper()
        self._wrapped = True
        
        print(f"[FleetOps] {self.name} wrapped successfully")
    
    def unwrap_cli(self) -> None:
        """Restore original CLI behavior"""
        if not self._wrapped:
            return
        
        # Remove wrapper
        self._remove_wrapper()
        self._wrapped = False
        
        print(f"[FleetOps] {self.name} unwrapped")
    
    def add_before_hook(self, hook: Callable) -> None:
        """Add a hook to run before executing a command"""
        self._before_hooks.append(hook)
    
    def add_after_hook(self, hook: Callable) -> None:
        """Add a hook to run after executing a command"""
        self._after_hooks.append(hook)
    
    def execute(self, command: str, *args, **kwargs) -> subprocess.CompletedProcess:
        """Execute a command with FleetOps governance"""
        
        # Run before hooks
        for hook in self._before_hooks:
            hook(command, *args, **kwargs)
        
        # Analyze command for danger
        danger_level = self._analyze_danger(command, args)
        
        if danger_level in ("safe", "low") and self.manifest and self.manifest.auto_approve_safe:
            # Auto-approve safe commands
            print(f"[FleetOps] Auto-approved: {command}")
            result = self._execute_original(command, *args, **kwargs)
        else:
            # Request approval
            approved = self._request_approval(command, danger_level)
            if approved:
                result = self._execute_original(command, *args, **kwargs)
            else:
                result = subprocess.CompletedProcess(
                    args=[command],
                    returncode=1,
                    stderr="FleetOps: Command blocked by approval policy"
                )
        
        # Run after hooks
        for hook in self._after_hooks:
            hook(result)
        
        return result
    
    def _find_cli_binary(self) -> Optional[str]:
        """Find the CLI binary in PATH"""
        import shutil
        return shutil.which(self.cli_command)
    
    def _analyze_danger(self, command: str, args: tuple) -> str:
        """Analyze command for danger level"""
        if not self.manifest or not self.manifest.danger_rules:
            return "medium"
        
        full_command = f"{command} {' '.join(str(a) for a in args)}"
        
        for rule in self.manifest.danger_rules:
            pattern = rule.get("pattern", "")
            level = rule.get("level", "medium")
            
            import re
            if re.search(pattern, full_command, re.IGNORECASE):
                return level
        
        return "safe"
    
    def _request_approval(self, command: str, danger_level: str) -> bool:
        """Request approval from FleetOps"""
        # This would call the FleetOps API
        print(f"[FleetOps] Approval required for: {command} (danger: {danger_level})")
        
        # For now, simulate approval
        # In production, this would show a prompt or send to Slack
        if danger_level in ("high", "critical"):
            print(f"[FleetOps] ⚠️  High risk command detected: {command}")
            print(f"[FleetOps] Use 'fleetops approve' or check Slack for approval")
            return False
        
        return True
    
    def _execute_original(self, command: str, *args, **kwargs) -> subprocess.CompletedProcess:
        """Execute the original CLI command"""
        if self._original_cli:
            full_cmd = [self._original_cli, command] + list(args)
            return subprocess.run(full_cmd, capture_output=True, text=True)
        else:
            return subprocess.CompletedProcess(
                args=[command],
                returncode=1,
                stderr="Original CLI not found"
            )
    
    def _create_wrapper(self) -> None:
        """Create wrapper script/alias"""
        # Create shell alias or wrapper script
        wrapper_dir = os.path.expanduser("~/.fleetops/wrappers")
        os.makedirs(wrapper_dir, exist_ok=True)
        
        wrapper_script = f"""#!/bin/bash
# FleetOps wrapper for {self.name}
# Auto-generated - do not edit manually

# Route through FleetOps
fleetops execute --connector={self.name} "$@"
"""
        
        wrapper_path = os.path.join(wrapper_dir, self.cli_command)
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_script)
        os.chmod(wrapper_path, 0o755)
        
        print(f"[FleetOps] Wrapper created at: {wrapper_path}")
    
    def _remove_wrapper(self) -> None:
        """Remove wrapper script"""
        wrapper_dir = os.path.expanduser("~/.fleetops/wrappers")
        wrapper_path = os.path.join(wrapper_dir, self.cli_command)
        if os.path.exists(wrapper_path):
            os.remove(wrapper_path)


class ShellIntegrationConnector(BaseConnector):
    """Connector that integrates with shell (bash, zsh, fish)"""
    
    @property
    def name(self) -> str:
        return "shell"
    
    @property
    def cli_command(self) -> str:
        return "bash"
    
    def install_shell_hook(self, shell: str = "bash") -> None:
        """Install shell hook for command interception"""
        
        hook_dir = os.path.expanduser(f"~/.fleetops/hooks")
        os.makedirs(hook_dir, exist_ok=True)
        
        if shell == "bash":
            hook = """
# FleetOps shell integration
# Add to ~/.bashrc: source ~/.fleetops/hooks/bash-hook.sh

fleetops_preexec() {
    local cmd="$1"
    # Send to FleetOps for approval
    fleetops check --command "$cmd" --shell
}

trap 'fleetops_preexec "$BASH_COMMAND"' DEBUG
"""
            hook_path = os.path.join(hook_dir, "bash-hook.sh")
        elif shell == "zsh":
            hook = """
# FleetOps shell integration for zsh
# Add to ~/.zshrc: source ~/.fleetops/hooks/zsh-hook.zsh

preexec() {
    local cmd="$1"
    fleetops check --command "$cmd" --shell
}
"""
            hook_path = os.path.join(hook_dir, "zsh-hook.zsh")
        else:
            print(f"[FleetOps] Shell {shell} not yet supported")
            return
        
        with open(hook_path, 'w') as f:
            f.write(hook)
        
        print(f"[FleetOps] Shell hook installed at: {hook_path}")
        print(f"[FleetOps] Add this to your ~/.{shell}rc:")
        print(f"  source {hook_path}")
