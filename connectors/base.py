"""Base Connector for FleetOps

All agent connectors should inherit from this class.
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from datetime import datetime
import requests

try:
    import websockets
except ImportError:
    websockets = None

class FleetOpsConnector(ABC):
    """Base class for all FleetOps agent connectors"""
    
    PROVIDER: str = "unknown"
    DEFAULT_MODEL: str = "unknown"
    
    def __init__(self, api_key: str, fleetops_url: str, org_id: str,
                 agent_name: str, agent_level: str = "junior",
                 parent_agent_id: Optional[str] = None):
        self.api_key = api_key
        self.fleetops_url = fleetops_url.rstrip("/")
        self.org_id = org_id
        self.agent_name = agent_name
        self.agent_level = agent_level
        self.parent_agent_id = parent_agent_id
        self.agent_id = None
        self.ws = None
        self.capabilities: List[str] = []
        self.sub_agents: Dict[str, 'FleetOpsConnector'] = {}
        self.max_sub_agents = 5
        self.event_handlers: Dict[str, Callable] = {}
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for events from FleetOps"""
        self.event_handlers[event_type] = handler
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return []
    
    async def connect(self):
        """Register with FleetOps and establish WebSocket"""
        response = requests.post(
            f"{self.fleetops_url}/api/v1/agents/",
            json={
                "name": self.agent_name,
                "provider": self.PROVIDER,
                "model": self.DEFAULT_MODEL,
                "capabilities": self.get_capabilities(),
                "level": self.agent_level,
                "parent_agent_id": self.parent_agent_id
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Org-ID": self.org_id
            }
        )
        response.raise_for_status()
        self.agent_id = response.json().get("id")
        
        if websockets:
            ws_url = self.fleetops_url.replace("https://", "wss://").replace("http://", "ws://")
            self.ws = await websockets.connect(f"{ws_url}/ws/agent/{self.agent_id}")
            asyncio.create_task(self._listen())
        
        return self.agent_id
    
    async def _listen(self):
        """Listen for messages from FleetOps"""
        if not self.ws:
            return
        try:
            async for message in self.ws:
                data = json.loads(message)
                event_type = data.get("type")
                
                if event_type in self.event_handlers:
                    await self.event_handlers[event_type](data)
                else:
                    await self._handle_default_event(data)
        except Exception as e:
            print(f"Connector error: {e}")
    
    async def _handle_default_event(self, data: dict):
        """Default event handler - override in subclasses"""
        print(f"Unhandled event: {data.get('type')}")
    
    async def create_sub_agent(self, connector_class, name: str, level: str = "junior"):
        """Create a sub-agent under this agent"""
        if len(self.sub_agents) >= self.max_sub_agents:
            raise ValueError(f"Max sub-agents ({self.max_sub_agents}) reached")
        
        sub_connector = connector_class(
            api_key=self.api_key,
            fleetops_url=self.fleetops_url,
            org_id=self.org_id,
            agent_name=name,
            agent_level=level,
            parent_agent_id=self.agent_id
        )
        sub_agent_id = await sub_connector.connect()
        self.sub_agents[sub_agent_id] = sub_connector
        return sub_connector
    
    async def request_approval(self, task_id: str, stage: str,
                              required_role: str = "operator",
                              sla_minutes: int = 30):
        """Request human approval for a task stage"""
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "request_approval",
                "task_id": task_id,
                "stage": stage,
                "required_role": required_role,
                "sla_minutes": sla_minutes
            }))
    
    async def report_task_event(self, task_id: str, status: str, stage: str, data: dict = None):
        """Report task progress to FleetOps"""
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "task_event",
                "task_id": task_id,
                "status": status,
                "stage": stage,
                "data": data or {}
            }))
    
    async def log_llm_usage(self, task_id: str, model: str,
                           tokens_in: int, tokens_out: int,
                           cost: float, latency_ms: int):
        """Log LLM usage for cost tracking"""
        requests.post(
            f"{self.fleetops_url}/api/v1/llm-usage/",
            json={
                "task_id": task_id,
                "agent_id": self.agent_id,
                "provider": self.PROVIDER,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": cost,
                "latency_ms": latency_ms
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Org-ID": self.org_id
            }
        )
    
    async def disconnect(self):
        """Disconnect from FleetOps"""
        if self.ws:
            await self.ws.close()
