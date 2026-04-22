"""OpenClaw Adapter for FleetOps

Integration with OpenClaw agent framework
OpenClaw is an autonomous agent system that works in sessions

Usage:
    1. Set OPENCLAW_URL and OPENCLAW_API_KEY in .env
    2. Agent appears in FleetOps agent list
    3. Tasks assigned to OpenClaw are executed in governed sessions
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from enum import Enum

class OpenClawExecutionStatus(str, Enum):
    """OpenClaw execution states"""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OpenClawAdapter:
    """FleetOps adapter for OpenClaw agent
    
    OpenClaw works in sessions with multiple steps.
    Each step can be paused for human approval via FleetOps.
    """
    
    def __init__(self):
        self.base_url = os.getenv("OPENCLAW_URL", "http://localhost:8080").rstrip("/")
        self.api_key = os.getenv("OPENCLAW_API_KEY", "")
        self.timeout = int(os.getenv("OPENCLAW_TIMEOUT", "300"))  # 5 min default
        self.max_steps = int(os.getenv("OPENCLAW_MAX_STEPS", "50"))
        
        # HTTP client with retries
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout = httpx.Timeout(self.timeout, connect=10)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            limits=limits,
            follow_redirects=True
        )
    
    async def create_session(self, task_id: str, instructions: str,
                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new OpenClaw session for a FleetOps task
        
        Args:
            task_id: FleetOps task ID (used for correlation)
            instructions: Natural language task description
            context: Additional context (files, URLs, history)
        
        Returns:
            Session object with id and status
        """
        try:
            payload = {
                "task_id": task_id,
                "instructions": instructions,
                "context": context or {},
                "mode": "governed",  # Tells OpenClaw to wait for approval at each step
                "max_steps": self.max_steps,
                "metadata": {
                    "source": "fleetops",
                    "version": "0.1.0",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post("/api/v1/sessions", json=payload)
            response.raise_for_status()
            
            return {
                "status": "created",
                "session_id": response.json().get("id"),
                "openclaw_data": response.json()
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"OpenClaw HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": f"OpenClaw connection timeout after {self.timeout}s"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        try:
            response = await self.client.get(f"/api/v1/sessions/{session_id}")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": data.get("status", "unknown"),
                "current_step": data.get("current_step", 0),
                "total_steps": data.get("total_steps", 0),
                "awaiting_approval": data.get("status") == "awaiting_approval",
                "output": data.get("output"),
                "error": data.get("error")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def execute_step(self, session_id: str, step_id: str,
                          approved: bool = True,
                          comments: Optional[str] = None) -> Dict[str, Any]:
        """Execute or skip a specific step in a session
        
        This is the core governance integration:
        - OpenClaw reaches a step that needs approval
        - FleetOps human reviews and decides
        - This method sends the decision back to OpenClaw
        """
        try:
            payload = {
                "step_id": step_id,
                "approved": approved,
                "comments": comments or "",
                "source": "fleetops",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            endpoint = f"/api/v1/sessions/{session_id}/steps/{step_id}/execute"
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            
            return {
                "status": "success",
                "step_completed": True,
                "result": response.json()
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"Step execution failed: HTTP {e.response.status_code}"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_step_details(self, session_id: str, step_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific step
        
        Used by FleetOps to show humans what the agent wants to do
        before asking for approval.
        """
        try:
            response = await self.client.get(
                f"/api/v1/sessions/{session_id}/steps/{step_id}"
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": "success",
                "step": {
                    "id": data.get("id"),
                    "description": data.get("description"),
                    "action_type": data.get("action_type"),  # file_edit, command, api_call, etc.
                    "proposed_changes": data.get("proposed_changes"),
                    "affected_files": data.get("affected_files", []),
                    "risk_level": self._assess_risk(data),
                    "can_auto_approve": self._can_auto_approve(data)
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cancel_session(self, session_id: str, reason: str = "") -> bool:
        """Cancel a running session"""
        try:
            response = await self.client.post(
                f"/api/v1/sessions/{session_id}/cancel",
                json={"reason": reason, "source": "fleetops"}
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_session_logs(self, session_id: str) -> List[Dict]:
        """Get execution logs for audit trail"""
        try:
            response = await self.client.get(f"/api/v1/sessions/{session_id}/logs")
            response.raise_for_status()
            return response.json().get("logs", [])
        except:
            return []
    
    async def submit_human_approval(self, session_id: str, step_id: str,
                                   decision: str,  # approve, reject, modify
                                   comments: Optional[str] = None,
                                   modifications: Optional[Dict] = None) -> Dict[str, Any]:
        """Submit human approval decision back to OpenClaw
        
        This is the critical governance loop:
        1. OpenClaw executes step
        2. Pauses for human review
        3. FleetOps shows step details to human
        4. Human decides: approve / reject / modify
        5. This method sends decision back
        6. OpenClaw continues or stops
        """
        try:
            payload = {
                "decision": decision,
                "comments": comments or "",
                "modifications": modifications or {},
                "approver": {
                    "system": "fleetops",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post(
                f"/api/v1/sessions/{session_id}/steps/{step_id}/approval",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "decision_recorded": True,
                "openclaw_response": response.json()
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"Approval submission failed: HTTP {e.response.status_code}"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _assess_risk(self, step_data: Dict) -> str:
        """Assess risk level of a proposed step
        
        Used by FleetOps to decide if auto-approval is safe
        or if human review is required.
        """
        action_type = step_data.get("action_type", "unknown")
        affected_files = step_data.get("affected_files", [])
        
        # High risk actions
        high_risk_actions = [
            "delete_file", "delete_directory", "database_migration",
            "api_deployment", "infrastructure_change", "permission_change"
        ]
        
        # Medium risk
        medium_risk_actions = [
            "file_edit", "command_execution", "api_call",
            "git_commit", "git_push", "package_install"
        ]
        
        if action_type in high_risk_actions:
            return "high"
        elif action_type in medium_risk_actions:
            # Check if production files
            prod_indicators = ["production", "prod", "main", "master", "live"]
            for file in affected_files:
                if any(ind in file.lower() for ind in prod_indicators):
                    return "high"
            return "medium"
        else:
            return "low"
    
    def _can_auto_approve(self, step_data: Dict) -> bool:
        """Determine if a step can be auto-approved
        
        Based on:
        - Risk level
        - Organization settings
        - User preferences
        """
        risk = self._assess_risk(step_data)
        
        # Only auto-approve low risk
        if risk == "low":
            # Check if it's a read-only operation
            action = step_data.get("action_type", "")
            read_only = ["read", "view", "list", "search", "analyze"]
            return any(ro in action for ro in read_only)
        
        return False
    
    async def close(self):
        """Close HTTP client connections"""
        await self.client.aclose()

# Singleton instance
openclaw_adapter = OpenClawAdapter()
