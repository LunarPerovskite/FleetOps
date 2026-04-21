"""WebSocket hub for real-time communication between FleetOps, agents, and humans"""

import json
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """Manages WebSocket connections for agents and humans"""
    
    def __init__(self):
        # agent_id -> websocket
        self.agent_connections: Dict[str, WebSocket] = {}
        # user_id -> websocket
        self.human_connections: Dict[str, WebSocket] = {}
        # org_id -> set of connected users
        self.org_connections: Dict[str, Set[str]] = {}
    
    async def connect_agent(self, agent_id: str, websocket: WebSocket):
        await websocket.accept()
        self.agent_connections[agent_id] = websocket
        print(f"Agent {agent_id} connected via WebSocket")
    
    async def connect_human(self, user_id: str, org_id: str, websocket: WebSocket):
        await websocket.accept()
        self.human_connections[user_id] = websocket
        if org_id not in self.org_connections:
            self.org_connections[org_id] = set()
        self.org_connections[org_id].add(user_id)
        print(f"Human {user_id} connected via WebSocket")
    
    def disconnect_agent(self, agent_id: str):
        self.agent_connections.pop(agent_id, None)
        print(f"Agent {agent_id} disconnected")
    
    def disconnect_human(self, user_id: str, org_id: str):
        self.human_connections.pop(user_id, None)
        if org_id in self.org_connections:
            self.org_connections[org_id].discard(user_id)
        print(f"Human {user_id} disconnected")
    
    async def send_to_agent(self, agent_id: str, message: dict):
        """Send a message to a specific agent"""
        if agent_id in self.agent_connections:
            await self.agent_connections[agent_id].send_json(message)
    
    async def send_to_human(self, user_id: str, message: dict):
        """Send a message to a specific human"""
        if user_id in self.human_connections:
            await self.human_connections[user_id].send_json(message)
    
    async def broadcast_to_org(self, org_id: str, message: dict):
        """Broadcast to all humans in an organization"""
        if org_id in self.org_connections:
            for user_id in self.org_connections[org_id]:
                await self.send_to_human(user_id, message)
    
    async def notify_approval_needed(self, task_id: str, stage: str, 
                                     required_role: str, sla_deadline: datetime,
                                     org_id: str):
        """Notify all humans who can approve at this level"""
        message = {
            "type": "approval_needed",
            "task_id": task_id,
            "stage": stage,
            "required_role": required_role,
            "sla_deadline": sla_deadline.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_org(org_id, message)
    
    async def notify_task_update(self, agent_id: str, task_id: str, 
                                 status: str, stage: str):
        """Notify agent of task status update"""
        message = {
            "type": "task_update",
            "task_id": task_id,
            "status": status,
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_agent(agent_id, message)

manager = ConnectionManager()
