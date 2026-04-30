"""FleetOps Python Client — Library for Agent Integration

Can be used by any agent or CLI:
- Claude Code, Roo Code (wrap their tool calls)
- CrewAI, AutoGen (wrap their execution)
- Custom agents (wrap their API calls)
- VS Code/Cursor extensions (wrap editor commands)

Usage:
    from fleetops_cli import FleetOpsClient
    
    # Initialize
    client = FleetOpsClient(api_url="http://fleetops.internal:8000")
    
    # Request approval before executing something
    approval = client.request_approval(
        agent_id="my-agent",
        action="bash",
        arguments="rm -rf /important",
        file_path="/important",
        environment="production"
    )
    
    if approval["can_proceed"]:
        # Execute the action
        result = client.execute_and_track(
            action="bash rm -rf /important",
            cost=0.0
        )
"""

import httpx
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ApprovalRequest:
    """Standardized approval request"""
    agent_id: str
    agent_name: str
    agent_type: str
    action: str
    arguments: Optional[str] = None
    file_path: Optional[str] = None
    environment: str = "development"
    estimated_cost: Optional[float] = None
    org_id: str = "default"


@dataclass
class ExecutionResult:
    """Result of tracked execution"""
    status: str
    output: str
    cost: float
    duration: float
    tokens_used: Optional[int] = None


class FleetOpsClient:
    """Client for interacting with FleetOps from any agent"""
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        org_id: str = "default"
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.org_id = org_id
        self._http_client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with auth"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def request_approval(self, **kwargs) -> Dict[str, Any]:
        """Request approval for an action
        
        Returns:
            {
                "status": "auto_approved" | "approved" | "rejected" | "timeout",
                "can_proceed": bool,
                "danger_level": str,
                "message": str
            }
        """
        request_data = {
            "agent_id": kwargs.get("agent_id", "unknown"),
            "agent_name": kwargs.get("agent_name", "Unknown Agent"),
            "agent_type": kwargs.get("agent_type", "generic"),
            "action": kwargs.get("action", "unknown"),
            "arguments": kwargs.get("arguments"),
            "file_path": kwargs.get("file_path"),
            "environment": kwargs.get("environment", "development"),
            "estimated_cost": kwargs.get("estimated_cost"),
            "org_id": self.org_id
        }
        
        try:
            response = await self._http_client.post(
                "/api/v1/approvals/request",
                json=request_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            # FleetOps not available — fail-safe: allow but warn
            return {
                "status": "fleetops_unavailable",
                "can_proceed": True,
                "danger_level": "unknown",
                "message": "FleetOps is not available. Proceeding without approval."
            }
        except Exception as e:
            return {
                "status": "error",
                "can_proceed": False,
                "error": str(e)
            }
    
    async def approve(
        self,
        approval_id: str,
        scope: str = "once",
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve a pending request"""
        try:
            response = await self._http_client.post(
                f"/api/v1/approvals/{approval_id}/approve",
                json={"scope": scope, "comments": comments}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def reject(
        self,
        approval_id: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject a pending request"""
        try:
            response = await self._http_client.post(
                f"/api/v1/approvals/{approval_id}/reject",
                json={"comments": comments}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def track_execution(
        self,
        agent_id: str,
        action: str,
        cost: float = 0.0,
        tokens: Optional[int] = None,
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Track execution after approval"""
        try:
            response = await self._http_client.post(
                "/api/v1/executions/track",
                json={
                    "agent_id": agent_id,
                    "action": action,
                    "cost": cost,
                    "tokens": tokens,
                    "duration": duration,
                    "org_id": self.org_id
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get list of pending approvals"""
        try:
            response = await self._http_client.get("/api/v1/approvals/pending")
            response.raise_for_status()
            return response.json().get("items", [])
        except Exception as e:
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get FleetOps system status"""
        try:
            response = await self._http_client.get("/health")
            response.raise_for_status()
            data = response.json()
            return {
                "status": data.get("status", "healthy"),
                "version": data.get("version", "unknown"),
                "agents": 0,
                "pending_approvals": 0,
                "total_cost_today": 0,
            }
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    async def list_discovered_models(self, provider: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List discovered models from the API"""
        try:
            params = {}
            if provider:
                params["provider"] = provider
            if search:
                params["query"] = search
            response = await self._http_client.get("/api/v1/models/discovered/search", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers"""
        try:
            response = await self._http_client.get("/api/v1/models/providers/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {}
    
    # ═══════════════════════════════════════════════════
    # SYNCHRONOUS WRAPPERS (for non-async agents)
    # ═══════════════════════════════════════════════════
    
    def request_approval_sync(self, **kwargs) -> Dict[str, Any]:
        """Synchronous version for non-async agents"""
        import asyncio
        return asyncio.run(self.request_approval(**kwargs))
    
    def approve_sync(self, approval_id: str, scope: str = "once", comments: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous approve"""
        import asyncio
        return asyncio.run(self.approve(approval_id, scope, comments))
    
    # ═══════════════════════════════════════════════════
    # CONTEXT MANAGER (for "with" statements)
    # ═══════════════════════════════════════════════════
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import asyncio
        asyncio.run(self._http_client.aclose())


# Convenience function for quick usage
def create_client(
    api_url: str = "http://localhost:8000",
    api_key: Optional[str] = None
) -> FleetOpsClient:
    """Create a FleetOps client with one line"""
    return FleetOpsClient(api_url=api_url, api_key=api_key)
