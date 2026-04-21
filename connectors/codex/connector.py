"""Codex Connector for FleetOps

Connects OpenAI's Codex to FleetOps governance platform.
"""

import os
import sys
import json
import asyncio
import websockets
from typing import Dict, List, Optional, Callable
from datetime import datetime
import requests

class CodexConnector:
    """Connector for OpenAI Codex agent"""
    
    PROVIDER = "openai"
    DEFAULT_MODEL = "gpt-5.1-codex"
    
    def __init__(self, api_key: str, fleetops_url: str, org_id: str,
                 agent_name: str = "Codex", agent_level: str = "senior",
                 parent_agent_id: Optional[str] = None):
        self.api_key = api_key
        self.fleetops_url = fleetops_url
        self.org_id = org_id
        self.agent_name = agent_name
        self.agent_level = agent_level
        self.parent_agent_id = parent_agent_id
        self.agent_id = None
        self.ws = None
        self.capabilities = ["code", "review", "debug", "refactor", "test", "architecture"]
        self.sub_agents: Dict[str, 'CodexConnector'] = {}
        self.max_sub_agents = 5
        self.event_handlers: Dict[str, Callable] = {}
        
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for events from FleetOps"""
        self.event_handlers[event_type] = handler
    
    async def connect(self):
        """Register with FleetOps and establish WebSocket"""
        response = requests.post(
            f"{self.fleetops_url}/api/v1/agents/",
            json={
                "name": self.agent_name,
                "provider": self.PROVIDER,
                "model": self.DEFAULT_MODEL,
                "capabilities": self.capabilities,
                "level": self.agent_level,
                "parent_agent_id": self.parent_agent_id
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Org-ID": self.org_id
            }
        )
        response.raise_for_status()
        agent_data = response.json()
        self.agent_id = agent_data.get("id")
        
        self.ws = await websockets.connect(
            f"{self.fleetops_url.replace('http', 'ws')}/ws/agent/{self.agent_id}"
        )
        
        asyncio.create_task(self._listen())
        return self.agent_id
    
    async def _listen(self):
        """Listen for messages from FleetOps"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                event_type = data.get("type")
                
                if event_type in self.event_handlers:
                    await self.event_handlers[event_type](data)
                elif event_type == "approval_response":
                    await self._handle_approval_response(data)
                elif event_type == "task_assigned":
                    await self._handle_task_assigned(data)
        except websockets.exceptions.ConnectionClosed:
            print(f"Codex connector disconnected")
    
    async def _handle_approval_response(self, data: dict):
        """Handle approval decision from human"""
        decision = data.get("decision")
        task_id = data.get("task_id")
        
        if decision == "approve":
            print(f"Task {task_id} approved")
        elif decision == "reject":
            print(f"Task {task_id} rejected")
        elif decision == "request_changes":
            print(f"Task {task_id} needs changes")
        elif decision == "escalate":
            await self.request_approval(task_id, "escalated", "senior")
    
    async def _handle_task_assigned(self, data: dict):
        """Handle task assignment"""
        task_id = data.get("task_id")
        parent_agent_id = data.get("parent_agent_id")
        print(f"Task {task_id} assigned from parent {parent_agent_id}")
    
    async def create_sub_agent(self, name: str, level: str = "junior"):
        """Create a sub-agent under this agent"""
        if len(self.sub_agents) >= self.max_sub_agents:
            raise ValueError(f"Max sub-agents ({self.max_sub_agents}) reached")
        
        sub_connector = CodexConnector(
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
        """Request human approval"""
        await self.ws.send(json.dumps({
            "type": "request_approval",
            "task_id": task_id,
            "stage": stage,
            "required_role": required_role,
            "sla_minutes": sla_minutes
        }))
    
    async def report_task_event(self, task_id: str, status: str, stage: str, data: dict = None):
        """Report task progress"""
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
        """Log LLM usage"""
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
        if self.ws:
            await self.ws.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Codex FleetOps Connector")
    parser.add_argument("--api-key", required=True, help="FleetOps API key")
    parser.add_argument("--url", default="https://api.fleetops.io", help="FleetOps URL")
    parser.add_argument("--org-id", required=True, help="Organization ID")
    parser.add_argument("--name", default="Codex", help="Agent name")
    parser.add_argument("--level", default="senior", choices=["junior", "senior", "lead"])
    parser.add_argument("--parent-agent", help="Parent agent ID")
    
    args = parser.parse_args()
    
    connector = CodexConnector(
        api_key=args.api_key,
        fleetops_url=args.url,
        org_id=args.org_id,
        agent_name=args.name,
        agent_level=args.level,
        parent_agent_id=args.parent_agent
    )
    
    asyncio.run(connector.connect())
    print(f"Codex connector running. Agent ID: {connector.agent_id}")
    
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        asyncio.run(connector.disconnect())
        print("Connector stopped")
