"""Hermes Adapter for FleetOps

Integration with Hermes agent framework
Hermes is a personal AI assistant that can execute commands and manage workflows

Usage:
    1. Set HERMES_URL and HERMES_API_KEY in .env
    2. Agent appears in FleetOps agent list
    3. Tasks assigned to Hermes are executed with human oversight
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from enum import Enum

class HermesExecutionStatus(str, Enum):
    """Hermes execution states"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class HermesAdapter:
    """FleetOps adapter for Hermes personal agent
    
    Hermes works as a personal assistant that:
    - Analyzes requests
    - Plans execution steps
    - Executes with optional human approval
    - Reports results back to FleetOps
    """
    
    def __init__(self):
        self.base_url = os.getenv("HERMES_URL", "http://localhost:9090").rstrip("/")
        self.api_key = os.getenv("HERMES_API_KEY", "")
        self.timeout = int(os.getenv("HERMES_TIMEOUT", "300"))
        self.persona = os.getenv("HERMES_PERSONA", "professional")
        
        # HTTP client
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout = httpx.Timeout(self.timeout, connect=10)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Hermes-Source": "fleetops"
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
    
    async def submit_task(self, task_id: str, instructions: str,
                         context: Optional[Dict] = None,
                         require_approval: bool = True) -> Dict[str, Any]:
        """Submit a task to Hermes for execution
        
        Args:
            task_id: FleetOps task ID
            instructions: Natural language task description
            context: Additional context
            require_approval: Whether to require human approval
        
        Returns:
            Task submission result with execution_id
        """
        try:
            payload = {
                "fleetops_task_id": task_id,
                "instructions": instructions,
                "context": context or {},
                "settings": {
                    "require_approval": require_approval,
                    "persona": self.persona,
                    "record_steps": True,
                    "max_execution_time": self.timeout
                },
                "metadata": {
                    "source": "fleetops",
                    "version": "0.1.0",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post("/api/v1/tasks", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": "submitted",
                "execution_id": data.get("execution_id"),
                "estimated_duration": data.get("estimated_duration"),
                "hermes_data": data
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"Hermes HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": f"Hermes connection timeout after {self.timeout}s"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current execution status from Hermes"""
        try:
            response = await self.client.get(f"/api/v1/tasks/{execution_id}")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": data.get("status", "unknown"),
                "progress": data.get("progress", 0),  # 0-100
                "current_step": data.get("current_step"),
                "total_steps": data.get("total_steps"),
                "awaiting_approval": data.get("status") == "awaiting_approval",
                "output": data.get("output"),
                "artifacts": data.get("artifacts", []),
                "error": data.get("error")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_pending_approvals(self, execution_id: str) -> List[Dict]:
        """Get list of pending approvals from Hermes
        
        Returns steps that need human review before continuing.
        """
        try:
            response = await self.client.get(
                f"/api/v1/tasks/{execution_id}/pending-approvals"
            )
            response.raise_for_status()
            return response.json().get("approvals", [])
            
        except:
            return []
    
    async def approve_step(self, execution_id: str, step_id: str,
                          approved: bool = True,
                          comments: Optional[str] = None,
                          modifications: Optional[Dict] = None) -> Dict[str, Any]:
        """Send approval decision for a specific step
        
        This is the governance integration point:
        - Hermes reaches a step that needs approval
        - FleetOps human reviews
        - This sends the decision back to Hermes
        """
        try:
            payload = {
                "step_id": step_id,
                "approved": approved,
                "comments": comments or "",
                "modifications": modifications or {},
                "approver": {
                    "system": "fleetops",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post(
                f"/api/v1/tasks/{execution_id}/approve",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "step_id": step_id,
                "approved": approved,
                "hermes_response": response.json()
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_execution_details(self, execution_id: str) -> Dict[str, Any]:
        """Get full execution details including all steps"""
        try:
            response = await self.client.get(f"/api/v1/tasks/{execution_id}/details")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": "success",
                "execution": {
                    "id": data.get("id"),
                    "instructions": data.get("instructions"),
                    "steps": data.get("steps", []),
                    "artifacts": data.get("artifacts", []),
                    "logs": data.get("logs", []),
                    "created_at": data.get("created_at"),
                    "completed_at": data.get("completed_at")
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cancel_execution(self, execution_id: str, reason: str = "") -> bool:
        """Cancel a running execution"""
        try:
            response = await self.client.post(
                f"/api/v1/tasks/{execution_id}/cancel",
                json={"reason": reason, "source": "fleetops"}
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_artifacts(self, execution_id: str) -> List[Dict]:
        """Get generated artifacts (files, reports, etc.)"""
        try:
            response = await self.client.get(f"/api/v1/tasks/{execution_id}/artifacts")
            response.raise_for_status()
            return response.json().get("artifacts", [])
        except:
            return []
    
    async def provide_feedback(self, execution_id: str,
                              feedback: str,
                              rating: Optional[int] = None) -> bool:
        """Provide feedback on execution quality"""
        try:
            response = await self.client.post(
                f"/api/v1/tasks/{execution_id}/feedback",
                json={
                    "feedback": feedback,
                    "rating": rating,
                    "source": "fleetops"
                }
            )
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """Close HTTP client connections"""
        await self.client.aclose()

# Singleton instance
hermes_adapter = HermesAdapter()
