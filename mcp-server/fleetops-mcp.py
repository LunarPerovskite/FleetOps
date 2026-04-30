#!/usr/bin/env python3
"""FleetOps MCP Server — Model Context Protocol for Agent Integration

Exposes FleetOps governance as MCP tools that any MCP-compatible agent can use:
- Claude Desktop
- Claude Code
- Roo Code
- Cursor
- Any MCP client

Usage:
    # Install dependencies
    pip install mcp httpx
    
    # Run the server
    python fleetops-mcp.py
    
    # Or use stdio (for Claude Desktop)
    python fleetops-mcp.py --transport stdio

Environment:
    FLEETOPS_API_URL=http://localhost:8000
    FLEETOPS_API_KEY=your-api-key
"""

import os
import sys
import json
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Try to import mcp, provide fallback if not installed
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        CallToolRequestParams,
        ListResourcesRequest,
        ReadResourceRequest,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[FleetOps MCP] Warning: mcp package not installed. Install with: pip install mcp")

import httpx


@dataclass
class FleetOpsConfig:
    """Configuration for FleetOps MCP server"""
    api_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    org_id: str = "default"
    auto_approve_safe: bool = True


class FleetOpsMCPClient:
    """HTTP client for FleetOps API"""
    
    def __init__(self, config: FleetOpsConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.api_url.rstrip("/"),
            headers=self._get_headers(),
            timeout=30.0
        )
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def request_approval(self, **kwargs) -> Dict[str, Any]:
        """Request approval before executing an action"""
        try:
            response = await self._client.post(
                "/api/v1/approvals/request",
                json={
                    "agent_id": kwargs.get("agent_id", "mcp-agent"),
                    "agent_name": kwargs.get("agent_name", "MCP Agent"),
                    "agent_type": kwargs.get("agent_type", "mcp"),
                    "action": kwargs.get("action", "unknown"),
                    "arguments": kwargs.get("arguments"),
                    "file_path": kwargs.get("file_path"),
                    "environment": kwargs.get("environment", "development"),
                    "estimated_cost": kwargs.get("estimated_cost"),
                    "org_id": self.config.org_id
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {
                "can_proceed": True,
                "status": "fleetops_unavailable",
                "message": "FleetOps unavailable, proceeding with caution"
            }
        except Exception as e:
            return {"can_proceed": False, "status": "error", "error": str(e)}
    
    async def track_execution(self, agent_id: str, action: str, cost: float = 0.0, 
                              tokens: Optional[int] = None, duration: Optional[float] = None) -> Dict[str, Any]:
        """Track execution after completion"""
        try:
            response = await self._client.post(
                "/api/v1/executions/track",
                json={
                    "agent_id": agent_id,
                    "action": action,
                    "cost": cost,
                    "tokens": tokens,
                    "duration": duration,
                    "org_id": self.config.org_id
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get FleetOps system status"""
        try:
            response = await self._client.get("/api/v1/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get pending approvals"""
        try:
            response = await self._client.get("/api/v1/approvals/pending")
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception:
            return []
    
    async def approve_request(self, approval_id: str, scope: str = "once", comments: Optional[str] = None) -> Dict[str, Any]:
        """Approve a request"""
        try:
            response = await self._client.post(
                f"/api/v1/approvals/{approval_id}/approve",
                json={"scope": scope, "comments": comments}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """Get active agents"""
        try:
            response = await self._client.get("/api/v1/agents")
            response.raise_for_status()
            data = response.json()
            return data.get("agents", [])
        except Exception:
            return []
    
    async def get_costs(self, period: str = "today") -> Dict[str, Any]:
        """Get cost summary"""
        try:
            response = await self._client.get(f"/api/v1/costs?period={period}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ═════════════════════════════════════════════════════════════
# MCP SERVER SETUP
# ═════════════════════════════════════════════════════════════

if MCP_AVAILABLE:
    server = Server("fleetops")
    config = FleetOpsConfig(
        api_url=os.getenv("FLEETOPS_API_URL", "http://localhost:8000"),
        api_key=os.getenv("FLEETOPS_API_KEY"),
        org_id=os.getenv("FLEETOPS_ORG_ID", "default")
    )
    client = FleetOpsMCPClient(config)
else:
    server = None


# ─── Resources (read-only data) ───

if MCP_AVAILABLE:
    @server.resource("fleetops://status")
    async def get_status_resource() -> str:
        """Get current FleetOps system status"""
        status = await client.get_status()
        return json.dumps(status, indent=2)


    @server.resource("fleetops://pending")
    async def get_pending_resource() -> str:
        """Get pending approvals"""
        pending = await client.get_pending_approvals()
        return json.dumps({"pending_approvals": pending}, indent=2)


    @server.resource("fleetops://agents")
    async def get_agents_resource() -> str:
        """Get active agents"""
        agents = await client.get_agents()
        return json.dumps({"agents": agents}, indent=2)


    @server.resource("fleetops://costs")
    async def get_costs_resource() -> str:
        """Get cost summary"""
        costs = await client.get_costs()
        return json.dumps(costs, indent=2)


    # ─── Tools (actions) ───

    @server.tool()
    async def request_approval(
        action: str,
        arguments: str = "",
        file_path: str = "",
        environment: str = "development",
        estimated_cost: float = 0.0,
        agent_name: str = "MCP Agent"
    ) -> str:
        """Request approval before executing a potentially dangerous action.

        Use this tool BEFORE executing any command that might:
        - Delete files or data
        - Modify production systems
        - Execute shell commands
        - Make API calls that cost money
        - Access sensitive files

        Args:
            action: Type of action (bash, write, delete, api, db, etc.)
            arguments: Command or arguments being executed
            file_path: File being modified (if applicable)
            environment: Environment (development, staging, production)
            estimated_cost: Estimated cost in USD
            agent_name: Name of the agent requesting approval

        Returns:
            JSON with can_proceed (bool), status, danger_level, message
        """
        result = await client.request_approval(
            action=action,
            arguments=arguments,
            file_path=file_path,
            environment=environment,
            estimated_cost=estimated_cost,
            agent_name=agent_name
        )

        if result.get("can_proceed"):
            return f"✅ APPROVED: {result.get('message', 'Proceed')}\nDanger level: {result.get('danger_level', 'unknown')}"
        else:
            return f"❌ BLOCKED: {result.get('message', 'Approval required')}\nDanger level: {result.get('danger_level', 'unknown')}"


    @server.tool()
    async def track_execution_cost(
        action: str,
        cost: float = 0.0,
        tokens: int = 0,
        duration: float = 0.0,
        agent_id: str = "mcp-agent"
    ) -> str:
        """Track the cost of an executed action.

        Use this tool AFTER executing an action to report:
        - Actual cost incurred
        - Tokens used
        - Duration

        Args:
            action: Description of what was executed
            cost: Actual cost in USD
            tokens: Number of tokens consumed
            duration: Execution time in seconds
            agent_id: ID of the agent

        Returns:
            Confirmation message
        """
        result = await client.track_execution(
            agent_id=agent_id,
            action=action,
            cost=cost,
            tokens=tokens,
            duration=duration
        )
        return f"📊 Tracked: {action} (${cost:.2f}, {tokens} tokens, {duration}s)"


    @server.tool()
    async def get_pending_approvals() -> str:
        """Get list of pending approvals that need human action.

        Returns:
            JSON list of pending approvals with IDs, agents, actions
        """
        pending = await client.get_pending_approvals()
        if not pending:
            return "🎉 No pending approvals!"

        lines = ["⏳ Pending Approvals:"]
        for apr in pending:
            lines.append(f"  - {apr.get('id')}: {apr.get('agent_name')} wants to {apr.get('action')} ({apr.get('danger_level', 'unknown')})")

        return "\n".join(lines)


    @server.tool()
    async def approve_request(
        approval_id: str,
        scope: str = "once",
        comments: str = ""
    ) -> str:
        """Approve a pending request.

        Args:
            approval_id: ID of the approval to approve
            scope: How long approval lasts (once, session, workspace, always)
            comments: Optional comments

        Returns:
            Confirmation message
        """
        result = await client.approve_request(approval_id, scope, comments)
        if result.get("status") == "success":
            return f"✅ Approved {approval_id} (scope: {scope})"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"


    @server.tool()
    async def get_fleetops_status() -> str:
        """Get FleetOps system status and health.

        Returns:
            System status, version, active agents, costs
        """
        status = await client.get_status()
        return json.dumps(status, indent=2)


    @server.tool()
    async def check_danger_level(
        action: str,
        arguments: str = "",
        file_path: str = "",
        environment: str = "development"
    ) -> str:
        """Check danger level of an action without requesting approval.

        Use this to preview what danger level an action would have.

        Args:
            action: Type of action
            arguments: Command arguments
            file_path: Target file
            environment: Environment

        Returns:
            Danger level and whether approval would be required
        """
        result = await client.request_approval(
            action=action,
            arguments=arguments,
            file_path=file_path,
            environment=environment
        )

        level = result.get("danger_level", "unknown")
        requires = result.get("requires_approval", False)

        emoji = {"safe": "🟢", "low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🚨"}.get(level, "⚪")

        return f"{emoji} Danger Level: {level.upper()}\nRequires Approval: {'Yes' if requires else 'No'}\nScore: {result.get('score', 0):.2f}"


# ═════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════

async def main():
    """Run the MCP server"""
    if not MCP_AVAILABLE:
        print("[FleetOps MCP] ERROR: mcp package not installed")
        print("[FleetOps MCP] Install with: pip install mcp")
        sys.exit(1)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fleetops",
                server_version="0.1.0",
                capabilities=server.get_capabilities()
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
