"""AutoGen Adapter for FleetOps

Integration with Microsoft AutoGen multi-agent conversation framework
AutoGen enables multiple LLMs to chat with each other to solve tasks

Usage:
    1. Set AUTOGEN_API_URL or run AutoGen with FastAPI wrapper
    2. Create agent groups (conversable agents)
    3. FleetOps governs the conversation and approvals
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from enum import Enum

class AutoGenStatus(str, Enum):
    """AutoGen execution states"""
    IDLE = "idle"
    CHATTING = "chatting"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

class AutoGenAdapter:
    """FleetOps adapter for Microsoft AutoGen
    
    AutoGen uses:
    - ConversableAgent: Agents that can chat
    - UserProxyAgent: Human-like agent for code execution
    - GroupChat: Multiple agents chatting together
    - GroupChatManager: Orchestrates the conversation
    
    FleetOps integration:
    1. Define agent group with roles
    2. Start conversation on a task
    3. Review each agent's proposed actions
    4. Approve code execution by UserProxyAgent
    """
    
    def __init__(self):
        self.base_url = os.getenv("AUTOGEN_URL", "http://localhost:8002").rstrip("/")
        self.api_key = os.getenv("AUTOGEN_API_KEY", "")
        self.timeout = int(os.getenv("AUTOGEN_TIMEOUT", "600"))
        self.max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "50"))
        
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
    
    async def create_agent_group(self, name: str,
                                agents: List[Dict],
                                max_rounds: Optional[int] = None,
                                speaker_selection: str = "auto",
                                config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a group of conversable agents
        
        Args:
            name: Group name
            agents: List of agent configurations
                [{"name": "coder", "system_message": "You are a coder...", "llm_config": {...}}]
            max_rounds: Max conversation rounds
            speaker_selection: How to select next speaker (auto, round_robin, manual)
            config: Additional config
        """
        try:
            payload = {
                "name": name,
                "agents": agents,
                "max_rounds": max_rounds or self.max_rounds,
                "speaker_selection_method": speaker_selection,
                "config": config or {},
                "metadata": {
                    "source": "fleetops",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post("/api/v1/groups", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "created",
                "group_id": data.get("id"),
                "group_data": data
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"AutoGen HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def start_conversation(self, task_id: str, group_id: str,
                                 message: str,
                                 require_code_approval: bool = True,
                                 require_message_approval: bool = False) -> Dict[str, Any]:
        """Start a group conversation on a task
        
        With FleetOps governance:
        - Code execution by UserProxyAgent requires approval
        - Each agent message can be reviewed (optional)
        - Human can intervene in the conversation
        """
        try:
            payload = {
                "fleetops_task_id": task_id,
                "group_id": group_id,
                "message": message,
                "governance": {
                    "require_code_approval": require_code_approval,
                    "require_message_approval": require_message_approval,
                    "record_conversation": True
                },
                "metadata": {
                    "source": "fleetops",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post("/api/v1/conversations", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "started",
                "conversation_id": data.get("id"),
                "group_id": group_id,
                "estimated_rounds": data.get("estimated_rounds"),
                "autogen_data": data
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"AutoGen HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation status and messages"""
        try:
            response = await self.client.get(f"/api/v1/conversations/{conversation_id}")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": data.get("status", "unknown"),
                "current_round": data.get("current_round", 0),
                "max_rounds": data.get("max_rounds", 0),
                "current_speaker": data.get("current_speaker"),
                "messages": data.get("messages", []),
                "awaiting_approval": data.get("status") == "awaiting_approval",
                "pending_code": data.get("pending_code"),
                "error": data.get("error")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_pending_actions(self, conversation_id: str) -> List[Dict]:
        """Get pending actions that need approval
        
        Includes:
        - Code execution proposals
        - File modifications
        - API calls
        """
        try:
            response = await self.client.get(
                f"/api/v1/conversations/{conversation_id}/pending-actions"
            )
            response.raise_for_status()
            return response.json().get("actions", [])
            
        except:
            return []
    
    async def approve_code_execution(self, conversation_id: str,
                                     action_id: str,
                                     approved: bool = True,
                                     comments: Optional[str] = None,
                                     modifications: Optional[Dict] = None) -> Dict[str, Any]:
        """Approve or reject code execution
        
        This is critical for security:
        - AutoGen's UserProxyAgent wants to run code
        - FleetOps shows the code to human
        - Human approves/rejects/modifies
        - AutoGen continues or stops
        """
        try:
            payload = {
                "action_id": action_id,
                "approved": approved,
                "comments": comments or "",
                "modifications": modifications or {},
                "approver": {
                    "system": "fleetops",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.client.post(
                f"/api/v1/conversations/{conversation_id}/actions/{action_id}/approve",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "action_id": action_id,
                "approved": approved
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def send_message(self, conversation_id: str,
                          message: str,
                          sender: str = "human") -> Dict[str, Any]:
        """Send a message to the conversation
        
        Allows human to intervene and chat with agents
        """
        try:
            payload = {
                "message": message,
                "sender": sender,
                "source": "fleetops",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await self.client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json=payload
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "message_sent": True
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_conversation_log(self, conversation_id: str) -> Dict[str, Any]:
        """Get full conversation log for audit"""
        try:
            response = await self.client.get(
                f"/api/v1/conversations/{conversation_id}/log"
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "messages": data.get("messages", []),
                "code_executions": data.get("code_executions", []),
                "summary": data.get("summary"),
                "final_output": data.get("final_output")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cancel_conversation(self, conversation_id: str,
                                 reason: str = "") -> bool:
        """Cancel a running conversation"""
        try:
            response = await self.client.post(
                f"/api/v1/conversations/{conversation_id}/cancel",
                json={"reason": reason, "source": "fleetops"}
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_agent_groups(self) -> List[Dict]:
        """Get list of configured agent groups"""
        try:
            response = await self.client.get("/api/v1/groups")
            response.raise_for_status()
            return response.json().get("groups", [])
        except:
            return []
    
    async def close(self):
        """Close HTTP client connections"""
        await self.client.aclose()

# Singleton
autogen_adapter = AutoGenAdapter()
