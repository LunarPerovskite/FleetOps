"""CrewAI Adapter for FleetOps

Integration with CrewAI multi-agent framework
CrewAI orchestrates multiple agents working together with roles and tasks

Usage:
    1. Set CREWAI_API_URL or run locally
    2. Create a crew of agents with different roles
    3. FleetOps governs the crew execution with human oversight
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from enum import Enum

class CrewAIStatus(str, Enum):
    """CrewAI execution states"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

class CrewAIAdapter:
    """FleetOps adapter for CrewAI multi-agent framework
    
    CrewAI organizes work into:
    - Agents with roles (researcher, writer, coder, etc.)
    - Tasks assigned to agents
    - Crews that orchestrate multiple agents
    - Processes (sequential, hierarchical, parallel)
    
    FleetOps integrates by:
    1. Defining a crew configuration
    2. Submitting tasks to the crew
    3. Reviewing agent outputs at each step
    4. Approving or rejecting crew actions
    """
    
    def __init__(self):
        self.base_url = os.getenv("CREWAI_URL", "http://localhost:8001").rstrip("/")
        self.api_key = os.getenv("CREWAI_API_KEY", "")
        self.timeout = int(os.getenv("CREWAI_TIMEOUT", "600"))  # 10 min default (crews take longer)
        self.default_process = os.getenv("CREWAI_PROCESS", "sequential")  # sequential, hierarchical, parallel
        
        # HTTP client
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout = httpx.Timeout(self.timeout, connect=10)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-FleetOps-Source": "fleetops"
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
    
    async def create_crew(self, name: str, description: str,
                       agents: List[Dict], process: str = "sequential",
                       config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a crew configuration
        
        Args:
            name: Crew name
            description: What this crew does
            agents: List of agent configurations
                [{"role": "researcher", "goal": "Find info", "backstory": "..."}]
            process: sequential, hierarchical, or parallel
            config: Additional configuration
        
        Returns:
            Crew object with id
        """
        try:
            payload = {
                "name": name,
                "description": description,
                "agents": agents,
                "process": process,
                "config": config or {},
                "metadata": {
                    "source": "fleetops",
                    "version": "0.1.0",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post("/api/v1/crews", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "created",
                "crew_id": data.get("id"),
                "crew_data": data
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"CrewAI HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def execute_crew_task(self, task_id: str, crew_id: str,
                             inputs: Dict[str, Any],
                             require_approval: bool = True) -> Dict[str, Any]:
        """Execute a task using a crew
        
        The crew will:
        1. Plan the work breakdown
        2. Assign subtasks to agents
        3. Execute sequentially or in parallel
        4. Return combined output
        
        With FleetOps governance:
        - Each agent action can be paused for approval
        - Human reviews intermediate outputs
        - Can cancel the entire crew
        """
        try:
            payload = {
                "fleetops_task_id": task_id,
                "crew_id": crew_id,
                "inputs": inputs,
                "governance": {
                    "require_approval": require_approval,
                    "approval_level": "task",  # task, step, or none
                    "record_outputs": True
                },
                "metadata": {
                    "source": "fleetops",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post("/api/v1/execute", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "executing",
                "execution_id": data.get("execution_id"),
                "crew_id": crew_id,
                "estimated_duration": data.get("estimated_duration"),
                "crewai_data": data
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"CrewAI HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get crew execution status"""
        try:
            response = await self.client.get(f"/api/v1/execute/{execution_id}")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": data.get("status", "unknown"),
                "progress": data.get("progress", 0),
                "current_agent": data.get("current_agent"),
                "current_task": data.get("current_task"),
                "completed_tasks": data.get("completed_tasks", []),
                "pending_tasks": data.get("pending_tasks", []),
                "awaiting_approval": data.get("status") == "awaiting_approval",
                "outputs": data.get("outputs", {}),
                "error": data.get("error")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_pending_approvals(self, execution_id: str) -> List[Dict]:
        """Get pending approvals from crew execution"""
        try:
            response = await self.client.get(
                f"/api/v1/execute/{execution_id}/pending-approvals"
            )
            response.raise_for_status()
            return response.json().get("approvals", [])
            
        except:
            return []
    
    async def approve_task(self, execution_id: str, task_id: str,
                          approved: bool = True,
                          comments: Optional[str] = None) -> Dict[str, Any]:
        """Approve or reject a specific crew task
        
        This allows granular control:
        - Approve one agent's output
        - Reject and retry with different agent
        - Modify the task description
        """
        try:
            payload = {
                "task_id": task_id,
                "approved": approved,
                "comments": comments or "",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await self.client.post(
                f"/api/v1/execute/{execution_id}/tasks/{task_id}/approve",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "task_id": task_id,
                "approved": approved
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_agent_outputs(self, execution_id: str) -> Dict[str, Any]:
        """Get outputs from each agent in the crew"""
        try:
            response = await self.client.get(
                f"/api/v1/execute/{execution_id}/outputs"
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "agent_outputs": data.get("outputs", {}),
                "final_output": data.get("final_output"),
                "execution_log": data.get("log", [])
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cancel_execution(self, execution_id: str, reason: str = "") -> bool:
        """Cancel a running crew execution"""
        try:
            response = await self.client.post(
                f"/api/v1/execute/{execution_id}/cancel",
                json={"reason": reason, "source": "fleetops"}
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_crew_list(self) -> List[Dict]:
        """Get list of configured crews"""
        try:
            response = await self.client.get("/api/v1/crews")
            response.raise_for_status()
            return response.json().get("crews", [])
        except:
            return []
    
    async def get_crew_details(self, crew_id: str) -> Dict[str, Any]:
        """Get crew configuration details"""
        try:
            response = await self.client.get(f"/api/v1/crews/{crew_id}")
            response.raise_for_status()
            return {
                "status": "success",
                "crew": response.json()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close HTTP client connections"""
        await self.client.aclose()

# Singleton
crewai_adapter = CrewAIAdapter()
