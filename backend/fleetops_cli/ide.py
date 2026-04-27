"""FleetOps IDE Integration — VS Code, Cursor, and other editors

Provides wrappers that can be injected into IDE extensions to intercept
and approve agent actions before execution.

Usage in VS Code extension (TypeScript/JavaScript):
    const FleetOps = require('fleetops-cli');
    const client = new FleetOps.Client({
        apiUrl: 'http://fleetops.internal:8000',
        apiKey: process.env.FLEETOPS_API_KEY
    });
    
    // Wrap any tool execution
    const approved = await client.requestApproval({
        agentId: 'vscode-copilot',
        action: 'terminal_execute',
        arguments: 'rm -rf node_modules',
        environment: 'development'
    });
    
    if (approved.canProceed) {
        // Execute the action
    }

Usage in Python agent (Claude Code, Roo Code):
    from fleetops_cli.ide import FleetOpsIDEExtension
    
    fleetops = FleetOpsIDEExtension()
    
    # Before executing a tool
    approval = fleetops.check_before_execute(
        tool="bash",
        command="rm -rf /important",
        file="/important"
    )
    
    if approval.can_proceed:
        # Safe to execute
        os.system("rm -rf /important")
"""

import asyncio
from typing import Optional, Dict, Any, Callable
from .client import FleetOpsClient


class FleetOpsIDEExtension:
    """FleetOps integration for IDE extensions and agents"""
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        agent_type: str = "ide_extension",
        auto_approve_safe: bool = True,
        show_notifications: bool = True
    ):
        self.client = FleetOpsClient(api_url=api_url, api_key=api_key)
        self.agent_type = agent_type
        self.auto_approve_safe = auto_approve_safe
        self.show_notifications = show_notifications
        self._pending_callbacks: Dict[str, Callable] = {}
    
    def check_before_execute(
        self,
        tool: str,
        command: str,
        file: Optional[str] = None,
        estimated_cost: float = 0.0,
        environment: str = "development"
    ) -> Dict[str, Any]:
        """Check if execution should proceed
        
        This is the main method IDE extensions should call before
        executing any action.
        
        Returns:
            {
                "can_proceed": bool,
                "status": str,
                "approval_id": Optional[str],
                "message": str
            }
        """
        # Map IDE tools to FleetOps actions
        action_map = {
            "terminal_execute": "bash",
            "file_write": "write",
            "file_delete": "delete",
            "api_call": "api",
            "code_execute": "code_execution",
            "db_query": "db",
        }
        
        action = action_map.get(tool, tool)
        
        # Build agent identifier
        agent_id = f"{self.agent_type}-{environment}"
        
        # Request approval
        import asyncio
        result = asyncio.run(self.client.request_approval(
            agent_id=agent_id,
            agent_name=self.agent_type,
            agent_type=self.agent_type,
            action=action,
            arguments=command,
            file_path=file,
            environment=environment,
            estimated_cost=estimated_cost
        ))
        
        if result.get("can_proceed"):
            if self.show_notifications and result.get("status") == "auto_approved":
                self._notify(f"Auto-approved: {command[:50]}")
        
        return result
    
    def wrap_function(self, func: Callable) -> Callable:
        """Decorator to wrap any function with FleetOps approval
        
        Usage:
            @fleetops.wrap_function
            def my_dangerous_function():
                os.system("rm -rf /tmp/data")
        """
        def wrapper(*args, **kwargs):
            # Extract action info from function
            action_name = func.__name__
            
            approval = self.check_before_execute(
                tool="code_execution",
                command=action_name,
                environment="development"
            )
            
            if approval.get("can_proceed"):
                return func(*args, **kwargs)
            else:
                raise PermissionError(f"FleetOps rejected: {approval.get('message')}")
        
        return wrapper
    
    def wrap_tool_call(self, tool_name: str, tool_func: Callable) -> Callable:
        """Wrap a specific tool (e.g., bash, write, read) with approval
        
        Usage:
            # In Claude Code, Roo Code, etc.
            tools.bash = fleetops.wrap_tool_call("bash", tools.bash)
            tools.write = fleetops.wrap_tool_call("write", tools.write)
        """
        def wrapper(*args, **kwargs):
            # Extract command from args
            command = str(args[0]) if args else str(kwargs.get("command", ""))
            
            approval = self.check_before_execute(
                tool=tool_name,
                command=command,
                environment="development"
            )
            
            if approval.get("can_proceed"):
                return tool_func(*args, **kwargs)
            else:
                return {
                    "status": "rejected",
                    "error": f"FleetOps rejected: {approval.get('message')}",
                    "output": ""
                }
        
        return wrapper
    
    def intercept_bash(self, command: str, **kwargs) -> Dict[str, Any]:
        """Intercept bash commands (specialized wrapper)"""
        return self.check_before_execute(
            tool="bash",
            command=command,
            **kwargs
        )
    
    def intercept_write(self, file_path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Intercept file writes (specialized wrapper)"""
        return self.check_before_execute(
            tool="write",
            command=f"Write {len(content)} bytes to {file_path}",
            file=file_path,
            **kwargs
        )
    
    def intercept_delete(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Intercept file deletes (specialized wrapper)"""
        return self.check_before_execute(
            tool="delete",
            command=f"Delete {file_path}",
            file=file_path,
            **kwargs
        )
    
    def _notify(self, message: str):
        """Show notification to user"""
        # This would integrate with IDE notification system
        # For now, print to stderr
        import sys
        print(f"[FleetOps] {message}", file=sys.stderr)
    
    def get_status(self) -> Dict[str, Any]:
        """Get FleetOps status for IDE status bar"""
        import asyncio
        return asyncio.run(self.client.get_status())
    
    def get_pending_count(self) -> int:
        """Get number of pending approvals (for badge)"""
        import asyncio
        pending = asyncio.run(self.client.get_pending())
        return len(pending)


# ═══════════════════════════════════════════════════
# QUICK SETUP FUNCTIONS
# ═══════════════════════════════════════════════════

def setup_for_vscode(api_url: str = "http://localhost:8000", **kwargs) -> FleetOpsIDEExtension:
    """Quick setup for VS Code extension"""
    return FleetOpsIDEExtension(
        api_url=api_url,
        agent_type="vscode_extension",
        **kwargs
    )


def setup_for_cursor(api_url: str = "http://localhost:8000", **kwargs) -> FleetOpsIDEExtension:
    """Quick setup for Cursor extension"""
    return FleetOpsIDEExtension(
        api_url=api_url,
        agent_type="cursor_extension",
        **kwargs
    )


def setup_for_claude_code(api_url: str = "http://localhost:8000", **kwargs) -> FleetOpsIDEExtension:
    """Quick setup for Claude Code"""
    return FleetOpsIDEExtension(
        api_url=api_url,
        agent_type="claude_code",
        **kwargs
    )


def setup_for_roo_code(api_url: str = "http://localhost:8000", **kwargs) -> FleetOpsIDEExtension:
    """Quick setup for Roo Code"""
    return FleetOpsIDEExtension(
        api_url=api_url,
        agent_type="roo_code",
        **kwargs
    )


# ═══════════════════════════════════════════════════
# TYPESCRIPT DEFINITIONS (for VS Code/Cursor extensions)
# ═══════════════════════════════════════════════════

TYPESCRIPT_DEFINITIONS = '''
// FleetOps TypeScript Definitions for VS Code/Cursor Extensions

interface FleetOpsConfig {
    apiUrl: string;
    apiKey?: string;
    agentType?: string;
    autoApproveSafe?: boolean;
    showNotifications?: boolean;
}

interface ApprovalResult {
    canProceed: boolean;
    status: string;
    approvalId?: string;
    dangerLevel?: string;
    message: string;
}

interface FleetOpsClient {
    requestApproval(params: {
        agentId: string;
        agentName: string;
        action: string;
        arguments?: string;
        filePath?: string;
        environment?: string;
        estimatedCost?: number;
    }): Promise<ApprovalResult>;
    
    approve(approvalId: string, scope?: string): Promise<any>;
    reject(approvalId: string, reason?: string): Promise<any>;
    getPending(): Promise<any[]>;
    getStatus(): Promise<any>;
}

declare module 'fleetops-cli' {
    export class FleetOpsClient {
        constructor(config: FleetOpsConfig);
        requestApproval(params: any): Promise<ApprovalResult>;
        approve(approvalId: string, scope?: string): Promise<any>;
        reject(approvalId: string, reason?: string): Promise<any>;
    }
    
    export class FleetOpsIDEExtension {
        constructor(config: FleetOpsConfig);
        checkBeforeExecute(tool: string, command: string, file?: string): Promise<ApprovalResult>;
        wrapFunction(func: Function): Function;
        wrapToolCall(toolName: string, toolFunc: Function): Function;
        getStatus(): Promise<any>;
        getPendingCount(): Promise<number>;
    }
}
'''
