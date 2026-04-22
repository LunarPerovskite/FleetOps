"""FleetOps Universal Connector Base

Supports both CLI and Cloud agent types.
Handles multi-tenant organizations with agents across different projects.
"""

import json
import asyncio
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class AgentMode(Enum):
    CLI = "cli"
    CLOUD = "cloud"
    HYBRID = "hybrid"

class AgentType(Enum):
    CODING = "coding"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    SUPPORT = "support"
    COMMUNITY = "community"
    VOICE = "voice"
    EMAIL = "email"
    CHAT = "chat"
    GENERAL = "general"

@dataclass
class AgentConfig:
    name: str
    provider: str
    model: str
    mode: AgentMode
    agent_type: AgentType
    capabilities: List[str]
    level: str = "junior"
    max_sub_agents: int = 5
    parent_agent_id: Optional[str] = None
    org_id: Optional[str] = None
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    source: str  # 'human', 'agent', 'system'
    content: str
    channel: str  # 'web', 'whatsapp', 'telegram', 'email', 'voice', 'cli', 'api'
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: str
    stage: str
    risk_level: str
    agent_id: str
    human_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    org_id: Optional[str] = None
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class FleetOpsConnector(ABC):
    """Universal connector for all agent types"""
    
    PROVIDER: str = "unknown"
    DEFAULT_MODEL: str = "unknown"
    
    def __init__(self, api_key: str, fleetops_url: str, config: AgentConfig):
        self.api_key = api_key
        self.fleetops_url = fleetops_url.rstrip("/")
        self.config = config
        self.agent_id: Optional[str] = None
        self.ws = None
        self.sub_agents: Dict[str, 'FleetOpsConnector'] = {}
        self.event_handlers: Dict[str, Callable] = {}
        self.message_handlers: Dict[str, Callable[[Message], None]] = {}
        self.task_handlers: Dict[str, Callable[[Task], None]] = {}
        self.is_running = False
        
    def register_event_handler(self, event_type: str, handler: Callable):
        self.event_handlers[event_type] = handler
    
    def register_message_handler(self, channel: str, handler: Callable[[Message], None]):
        self.message_handlers[channel] = handler
    
    def register_task_handler(self, status: str, handler: Callable[[Task], None]):
        self.task_handlers[status] = handler
    
    async def connect(self) -> str:
        """Register agent with FleetOps"""
        response = requests.post(
            f"{self.fleetops_url}/api/v1/agents/",
            json={
                "name": self.config.name,
                "provider": self.config.provider or self.PROVIDER,
                "model": self.config.model or self.DEFAULT_MODEL,
                "mode": self.config.mode.value,
                "agent_type": self.config.agent_type.value,
                "capabilities": self.config.capabilities,
                "level": self.config.level,
                "max_sub_agents": self.config.max_sub_agents,
                "parent_agent_id": self.config.parent_agent_id,
                "org_id": self.config.org_id,
                "team_id": self.config.team_id,
                "project_id": self.config.project_id,
                "metadata": self.config.metadata
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        agent_data = response.json()
        self.agent_id = agent_data.get("id")
        
        # Connect WebSocket
        ws_url = self.fleetops_url.replace("https://", "wss://").replace("http://", "ws://")
        try:
            import websockets
            self.ws = await websockets.connect(f"{ws_url}/ws/agent/{self.agent_id}")
            asyncio.create_task(self._listen())
        except ImportError:
            print("websockets not installed, using HTTP polling mode")
        
        self.is_running = True
        return self.agent_id
    
    async def _listen(self):
        """Listen for messages from FleetOps"""
        try:
            while self.is_running:
                if self.ws:
                    try:
                        import websockets
                        message = await asyncio.wait_for(self.ws.recv(), timeout=30)
                        data = json.loads(message)
                        await self._handle_message(data)
                    except asyncio.TimeoutError:
                        # Send heartbeat
                        if self.ws:
                            await self.ws.send(json.dumps({"type": "heartbeat"}))
                    except websockets.exceptions.ConnectionClosed:
                        print("WebSocket closed, reconnecting...")
                        await self._reconnect()
                else:
                    # HTTP polling fallback
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"Connector error: {e}")
            self.is_running = False
    
    async def _handle_message(self, data: dict):
        """Handle incoming messages"""
        msg_type = data.get("type")
        
        # Custom event handlers
        if msg_type in self.event_handlers:
            await self.event_handlers[msg_type](data)
            return
        
        # Default handlers
        handlers = {
            "approval_response": self._handle_approval_response,
            "task_assigned": self._handle_task_assigned,
            "subagent_assigned": self._handle_subagent_assigned,
            "message": self._handle_incoming_message,
            "escalation": self._handle_escalation,
            "heartbeat_ack": lambda x: None,
        }
        
        handler = handlers.get(msg_type, self._handle_unknown)
        await handler(data)
    
    async def _handle_approval_response(self, data: dict):
        decision = data.get("decision")
        task_id = data.get("task_id")
        
        if decision == "approve":
            print(f"✅ Task {task_id} approved by {data.get('human_id')}")
        elif decision == "reject":
            print(f"❌ Task {task_id} rejected")
        elif decision == "request_changes":
            print(f"📝 Task {task_id} needs changes")
        elif decision == "escalate":
            print(f"⬆️ Task {task_id} escalated")
            await self.request_approval(task_id, "escalated", "senior")
    
    async def _handle_task_assigned(self, data: dict):
        print(f"📋 Task {data.get('task_id')} assigned from parent {data.get('parent_agent_id')}")
    
    async def _handle_subagent_assigned(self, data: dict):
        print(f"👥 Sub-agent {data.get('sub_agent_id')} assigned")
    
    async def _handle_incoming_message(self, data: dict):
        """Handle incoming customer message"""
        msg = Message(
            source=data.get("source", "human"),
            content=data.get("content", ""),
            channel=data.get("channel", "unknown"),
            thread_id=data.get("thread_id"),
            metadata=data.get("metadata", {})
        )
        
        channel = msg.channel
        if channel in self.message_handlers:
            await self.message_handlers[channel](msg)
        else:
            # Default: log and respond
            print(f"📨 [{channel}] {msg.source}: {msg.content[:100]}")
    
    async def _handle_escalation(self, data: dict):
        """Handle escalation to human"""
        print(f"🚨 Escalation: Task {data.get('task_id')} -> {data.get('required_role')}")
    
    async def _handle_unknown(self, data: dict):
        print(f"❓ Unknown message type: {data.get('type')}")
    
    async def _reconnect(self):
        """Reconnect WebSocket"""
        import websockets
        ws_url = self.fleetops_url.replace("https://", "wss://").replace("http://", "ws://")
        try:
            self.ws = await websockets.connect(f"{ws_url}/ws/agent/{self.agent_id}")
            print(f"Reconnected agent {self.agent_id}")
        except Exception as e:
            print(f"Reconnect failed: {e}")
    
    # === Agent Hierarchy ===
    
    async def create_sub_agent(self, name: str, config: AgentConfig) -> 'FleetOpsConnector':
        """Create sub-agent under this agent"""
        # Unlimited sub-agents by default
        if self.config.max_sub_agents is not None and len(self.sub_agents) >= self.config.max_sub_agents:
            raise ValueError(f"Max sub-agents ({self.config.max_sub_agents}) reached")
        
        # Create connector for sub-agent
        sub_config = AgentConfig(
            name=name,
            provider=config.provider or self.config.provider,
            model=config.model or self.config.model,
            mode=config.mode,
            agent_type=config.agent_type or self.config.agent_type,
            capabilities=config.capabilities or self.config.capabilities,
            level="junior",
            parent_agent_id=self.agent_id,
            org_id=self.config.org_id,
            team_id=self.config.team_id,
            project_id=self.config.project_id
        )
        
        # Use same class as parent
        sub_connector = self.__class__(self.api_key, self.fleetops_url, sub_config)
        sub_agent_id = await sub_connector.connect()
        self.sub_agents[sub_agent_id] = sub_connector
        
        print(f"👶 Sub-agent {name} ({sub_agent_id}) created under {self.agent_id}")
        return sub_connector
    
    async def delegate_task(self, task_id: str, sub_agent_id: str) -> dict:
        """Delegate task to sub-agent"""
        if sub_agent_id not in self.sub_agents:
            raise ValueError(f"Sub-agent {sub_agent_id} not found")
        
        # Notify sub-agent
        sub = self.sub_agents[sub_agent_id]
        if sub.ws:
            await sub.ws.send(json.dumps({
                "type": "task_assigned",
                "task_id": task_id,
                "parent_agent_id": self.agent_id
            }))
        
        # Update task in FleetOps
        requests.patch(
            f"{self.fleetops_url}/api/v1/tasks/{task_id}/delegate",
            json={"sub_agent_id": sub_agent_id},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        return {"status": "delegated", "sub_agent_id": sub_agent_id}
    
    # === Approval System ===
    
    async def request_approval(self, task_id: str, stage: str,
                              required_role: str = "operator",
                              sla_minutes: int = 30,
                              context: dict = None):
        """Request human approval"""
        payload = {
            "type": "request_approval",
            "task_id": task_id,
            "stage": stage,
            "required_role": required_role,
            "sla_minutes": sla_minutes,
            "agent_id": self.agent_id,
            "context": context or {}
        }
        
        if self.ws:
            await self.ws.send(json.dumps(payload))
        else:
            # HTTP fallback
            requests.post(
                f"{self.fleetops_url}/api/v1/approvals/",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
    
    # === Communication ===
    
    async def send_message(self, content: str, channel: str = "web",
                          thread_id: str = None, human_id: str = None):
        """Send message to human via any channel"""
        payload = {
            "type": "send_message",
            "content": content,
            "channel": channel,
            "thread_id": thread_id,
            "human_id": human_id,
            "agent_id": self.agent_id
        }
        
        requests.post(
            f"{self.fleetops_url}/api/v1/messages/",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def report_task_event(self, task_id: str, status: str,
                               stage: str, data: dict = None):
        """Report task progress"""
        payload = {
            "type": "task_event",
            "task_id": task_id,
            "status": status,
            "stage": stage,
            "agent_id": self.agent_id,
            "data": data or {}
        }
        
        if self.ws:
            await self.ws.send(json.dumps(payload))
        else:
            requests.post(
                f"{self.fleetops_url}/api/v1/events/",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
    
    # === LLM Usage Tracking ===
    
    async def log_llm_usage(self, task_id: str, model: str,
                           tokens_in: int, tokens_out: int,
                           cost: float, latency_ms: int,
                           temperature: Optional[float] = None):
        """Log LLM usage for cost tracking"""
        requests.post(
            f"{self.fleetops_url}/api/v1/llm-usage/",
            json={
                "task_id": task_id,
                "agent_id": self.agent_id,
                "provider": self.config.provider or self.PROVIDER,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": cost,
                "latency_ms": latency_ms,
                "temperature": temperature
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    # === Organization & Project Context ===
    
    def set_org_context(self, org_id: str, team_id: str = None, project_id: str = None):
        """Set organization context for multi-tenant operations"""
        self.config.org_id = org_id
        self.config.team_id = team_id
        self.config.project_id = project_id
    
    async def get_org_agents(self) -> List[dict]:
        """Get all agents in same org"""
        response = requests.get(
            f"{self.fleetops_url}/api/v1/agents/",
            params={"org_id": self.config.org_id},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    async def get_org_humans(self) -> List[dict]:
        """Get all humans in same org with hierarchy"""
        response = requests.get(
            f"{self.fleetops_url}/api/v1/users/",
            params={"org_id": self.config.org_id},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    async def disconnect(self):
        """Disconnect from FleetOps"""
        self.is_running = False
        if self.ws:
            import websockets
            await self.ws.close()
        for sub in self.sub_agents.values():
            await sub.disconnect()
