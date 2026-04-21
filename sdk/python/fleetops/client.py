"""FleetOps Client"""

import requests
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime

class FleetOpsClient:
    """Main client for FleetOps API"""
    
    def __init__(self, api_key: str, org_id: str, base_url: str = "https://api.fleetops.io"):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Org-ID": org_id
        }
    
    def connect_agent(self, name: str, provider: str, model: str, 
                     capabilities: List[str], level: str = "junior",
                     callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Register an agent with FleetOps"""
        payload = {
            "name": name,
            "provider": provider,
            "model": model,
            "capabilities": capabilities,
            "level": level,
            "callback_url": callback_url
        }
        response = requests.post(
            f"{self.base_url}/api/v1/agents/",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def report_event(self, event_type: str, data: Dict[str, Any],
                    task_id: Optional[str] = None,
                    agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Report an event to FleetOps"""
        payload = {
            "event_type": event_type,
            "data": data,
            "task_id": task_id,
            "agent_id": agent_id
        }
        response = requests.post(
            f"{self.base_url}/api/v1/events/",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def request_approval(self, task_id: str, stage: str,
                        role_needed: str = "operator",
                        sla_minutes: int = 30,
                        data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Request human approval for a task stage"""
        payload = {
            "task_id": task_id,
            "stage": stage,
            "role_needed": role_needed,
            "sla_minutes": sla_minutes,
            "data": data or {}
        }
        response = requests.post(
            f"{self.base_url}/api/v1/approvals/",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task details with events and approvals"""
        response = requests.get(
            f"{self.base_url}/api/v1/tasks/{task_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def log_llm_usage(self, provider: str, model: str, task_id: str,
                     agent_id: str, tokens_in: int, tokens_out: int,
                     cost: float, latency_ms: int,
                     temperature: Optional[float] = None) -> Dict[str, Any]:
        """Log LLM usage for cost tracking"""
        payload = {
            "provider": provider,
            "model": model,
            "task_id": task_id,
            "agent_id": agent_id,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "latency_ms": latency_ms,
            "temperature": temperature
        }
        response = requests.post(
            f"{self.base_url}/api/v1/llm-usage/",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
