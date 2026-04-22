"""Personal Agent Adapter for FleetOps

Generic adapter for personal AI agents that:
- Run on user's machine (localhost)
- Have their own UI but accept API commands
- Need human oversight for sensitive operations

Supported agent types:
- OpenClaw (session-based)
- Hermes (task-based)
- Custom agents with HTTP API
- Local LLM agents (Ollama, etc.)

This adapter provides a unified interface for FleetOps
while allowing each agent to have its own protocol.
"""

import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import httpx
from enum import Enum

class AgentType(str, Enum):
    """Supported agent types"""
    # Personal
    OPENCLAW = "openclaw"
    HERMES = "hermes"
    # Multi-Agent
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    METAGPT = "metagpt"
    CHATDEV = "chatdev"
    GPTEAM = "gpteam"
    AGENTVERSE = "agentverse"
    PRAISONAI = "praisonai"
    # Frameworks
    LANGCHAIN = "langchain"
    LLAMAINDEX = "llamaindex"
    TASKWEAVER = "taskweaver"
    # Autonomous
    BABYAGI = "babyagi"
    SUPERAGI = "superagi"
    # Local LLM
    OLLAMA = "ollama"
    LOCAL_LLM = "local_llm"
    # Custom
    CUSTOM = "custom"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class PersonalAgentAdapter:
    """Unified adapter for personal AI agents
    
    This adapter wraps specific adapters (OpenClaw, Hermes, etc.)
    and provides a common interface for FleetOps.
    
    Usage:
        adapter = PersonalAgentAdapter("openclaw")
        result = await adapter.execute_task(task_id, instructions)
    """
    
    def __init__(self, agent_type: Union[str, AgentType], config: Optional[Dict] = None):
        self.agent_type = AgentType(agent_type) if isinstance(agent_type, str) else agent_type
        self.config = config or {}
        self._adapter = None
        self._initialize_adapter()
    
    def _initialize_adapter(self):
        """Initialize the specific adapter based on agent type"""
        # Personal agents
        if self.agent_type in [AgentType.OPENCLAW]:
            from app.adapters.openclaw_adapter import openclaw_adapter
            self._adapter = openclaw_adapter
        elif self.agent_type in [AgentType.HERMES]:
            from app.adapters.hermes_adapter import hermes_adapter
            self._adapter = hermes_adapter
        # Multi-Agent frameworks
        elif self.agent_type == AgentType.CREWAI:
            from app.adapters.crewai_adapter import crewai_adapter
            self._adapter = crewai_adapter
        elif self.agent_type == AgentType.AUTOGEN:
            from app.adapters.autogen_adapter import autogen_adapter
            self._adapter = autogen_adapter
        elif self.agent_type == AgentType.METAGPT:
            from app.adapters.all_adapters import metagpt_adapter
            self._adapter = metagpt_adapter
        elif self.agent_type == AgentType.CHATDEV:
            from app.adapters.all_adapters import chatdev_adapter
            self._adapter = chatdev_adapter
        elif self.agent_type == AgentType.GPTEAM:
            from app.adapters.all_adapters import gpteam_adapter
            self._adapter = gpteam_adapter
        elif self.agent_type == AgentType.AGENTVERSE:
            from app.adapters.all_adapters import agentverse_adapter
            self._adapter = agentverse_adapter
        elif self.agent_type == AgentType.PRAISONAI:
            from app.adapters.all_adapters import praisonai_adapter
            self._adapter = praisonai_adapter
        # Frameworks
        elif self.agent_type == AgentType.LANGCHAIN:
            from app.adapters.all_adapters import langchain_adapter
            self._adapter = langchain_adapter
        elif self.agent_type == AgentType.LLAMAINDEX:
            from app.adapters.all_adapters import llamaindex_adapter
            self._adapter = llamaindex_adapter
        elif self.agent_type == AgentType.TASKWEAVER:
            from app.adapters.all_adapters import taskweaver_adapter
            self._adapter = taskweaver_adapter
        # Autonomous
        elif self.agent_type == AgentType.BABYAGI:
            from app.adapters.all_adapters import babyagi_adapter
            self._adapter = babyagi_adapter
        elif self.agent_type == AgentType.SUPERAGI:
            from app.adapters.all_adapters import superagi_adapter
            self._adapter = superagi_adapter
        # Local LLM
        elif self.agent_type == AgentType.OLLAMA:
            self._adapter = OllamaAdapter(self.config)
        elif self.agent_type == AgentType.LOCAL_LLM:
            from app.adapters.all_adapters import local_llm_adapter
            self._adapter = local_llm_adapter
        # Custom / Default
        else:
            self._adapter = CustomAgentAdapter(self.config)
    
    async def execute_task(self, task_id: str, instructions: str,
                        context: Optional[Dict] = None,
                        require_approval: bool = True) -> Dict[str, Any]:
        """Execute a task using the configured agent
        
        This is the main interface that FleetOps uses.
        All agent-specific details are handled internally.
        """
        if not self._adapter:
            return {
                "status": "error",
                "error": f"Agent type {self.agent_type} not supported or not configured"
            }
        
        try:
            # Call the appropriate adapter method
            if self.agent_type == AgentType.OPENCLAW:
                # OpenClaw uses sessions
                result = await self._adapter.create_session(
                    task_id=task_id,
                    instructions=instructions,
                    context=context
                )
                
                if result["status"] == "created":
                    return {
                        "status": "executing",
                        "task_id": task_id,
                        "session_id": result["session_id"],
                        "agent_type": self.agent_type.value,
                        "requires_approval": require_approval,
                        "check_status": f"/api/v1/agent-status/{result['session_id']}"
                    }
                else:
                    return result
                    
            elif self.agent_type == AgentType.HERMES:
                # Hermes uses task submission
                result = await self._adapter.submit_task(
                    task_id=task_id,
                    instructions=instructions,
                    context=context,
                    require_approval=require_approval
                )
                
                if result["status"] == "submitted":
                    return {
                        "status": "executing",
                        "task_id": task_id,
                        "execution_id": result["execution_id"],
                        "agent_type": self.agent_type.value,
                        "requires_approval": require_approval,
                        "estimated_duration": result.get("estimated_duration")
                    }
                else:
                    return result
                    
            else:
                # Generic adapter
                result = await self._adapter.execute(instructions, context)
                return {
                    "status": result.get("status", "unknown"),
                    "task_id": task_id,
                    "agent_type": self.agent_type.value,
                    "output": result.get("output"),
                    "requires_approval": require_approval
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Agent execution failed: {str(e)}",
                "agent_type": self.agent_type.value
            }
    
    async def get_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status"""
        if not self._adapter:
            return {"status": "error", "error": "Agent not configured"}
        
        try:
            if self.agent_type == AgentType.OPENCLAW:
                return await self._adapter.get_session_status(execution_id)
            elif self.agent_type == AgentType.HERMES:
                return await self._adapter.get_execution_status(execution_id)
            else:
                return await self._adapter.get_status(execution_id)
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_pending_approvals(self, execution_id: str) -> List[Dict]:
        """Get pending approvals that need human review"""
        if not self._adapter:
            return []
        
        try:
            if self.agent_type == AgentType.OPENCLAW:
                # OpenClaw: check session status for awaiting_approval
                status = await self._adapter.get_session_status(execution_id)
                if status.get("awaiting_approval"):
                    # Get current step details
                    step = await self._adapter.get_step_details(
                        execution_id,
                        status.get("current_step")
                    )
                    if step["status"] == "success":
                        return [{
                            "step_id": step["step"]["id"],
                            "description": step["step"]["description"],
                            "action_type": step["step"]["action_type"],
                            "risk_level": step["step"]["risk_level"],
                            "can_auto_approve": step["step"]["can_auto_approve"]
                        }]
                return []
                
            elif self.agent_type == AgentType.HERMES:
                # Hermes: get pending approvals directly
                return await self._adapter.get_pending_approvals(execution_id)
                
            else:
                return await self._adapter.get_pending_approvals(execution_id)
                
        except:
            return []
    
    async def approve(self, execution_id: str, step_id: str,
                     decision: str,  # approve, reject, modify
                     comments: Optional[str] = None,
                     modifications: Optional[Dict] = None) -> Dict[str, Any]:
        """Send human approval decision to agent
        
        This is the key governance method:
        - Human reviews in FleetOps UI
        - Clicks approve/reject/modify
        - This sends decision to agent
        - Agent continues or stops
        """
        if not self._adapter:
            return {"status": "error", "error": "Agent not configured"}
        
        try:
            if self.agent_type == AgentType.OPENCLAW:
                return await self._adapter.submit_human_approval(
                    session_id=execution_id,
                    step_id=step_id,
                    decision=decision,
                    comments=comments,
                    modifications=modifications
                )
            elif self.agent_type == AgentType.HERMES:
                return await self._adapter.approve_step(
                    execution_id=execution_id,
                    step_id=step_id,
                    approved=(decision == "approve"),
                    comments=comments,
                    modifications=modifications
                )
            else:
                return await self._adapter.approve(
                    execution_id, step_id, decision, comments
                )
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cancel(self, execution_id: str, reason: str = "") -> bool:
        """Cancel running execution"""
        if not self._adapter:
            return False
        
        try:
            if self.agent_type == AgentType.OPENCLAW:
                return await self._adapter.cancel_session(execution_id, reason)
            elif self.agent_type == AgentType.HERMES:
                return await self._adapter.cancel_execution(execution_id, reason)
            else:
                return await self._adapter.cancel(execution_id, reason)
        except:
            return False
    
    async def get_logs(self, execution_id: str) -> List[Dict]:
        """Get execution logs for audit"""
        if not self._adapter:
            return []
        
        try:
            if self.agent_type == AgentType.OPENCLAW:
                return await self._adapter.get_session_logs(execution_id)
            elif self.agent_type == AgentType.HERMES:
                details = await self._adapter.get_execution_details(execution_id)
                if details["status"] == "success":
                    return details["execution"].get("logs", [])
                return []
            else:
                return await self._adapter.get_logs(execution_id)
        except:
            return []
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities based on type"""
        capabilities = {
            # Personal
            AgentType.OPENCLAW: [
                "session_based_execution",
                "step_by_step_approval",
                "file_editing",
                "command_execution",
                "git_operations",
                "multi_step_planning"
            ],
            AgentType.HERMES: [
                "task_based_execution",
                "progress_tracking",
                "artifact_generation",
                "workflow_automation",
                "scheduled_execution"
            ],
            # Multi-Agent
            AgentType.CREWAI: [
                "multi_agent_crew",
                "role_based_agents",
                "task_delegation",
                "sequential_execution",
                "hierarchical_execution",
                "parallel_execution",
                "agent_collaboration"
            ],
            AgentType.AUTOGEN: [
                "multi_agent_chat",
                "conversable_agents",
                "group_chat",
                "code_execution",
                "human_proxy",
                "agent_debate"
            ],
            AgentType.METAGPT: [
                "software_company_simulation",
                "role_playing",
                "product_manager",
                "architect",
                "engineer",
                "qa_engineer",
                "deliverable_approval"
            ],
            AgentType.CHATDEV: [
                "chat_based_dev",
                "software_phases",
                "phase_approval",
                "code_generation"
            ],
            AgentType.GPTEAM: [
                "hierarchical_teams",
                "team_lead",
                "worker_agents",
                "task_assignment"
            ],
            AgentType.AGENTVERSE: [
                "multi_agent_env",
                "agent_simulation",
                "collaborative_problem_solving"
            ],
            AgentType.PRAISONAI: [
                "auto_generated_crews",
                "role_discovery",
                "automatic_agents"
            ],
            # Frameworks
            AgentType.LANGCHAIN: [
                "chains",
                "agents",
                "tools",
                "memory",
                "rag",
                "tool_approval"
            ],
            AgentType.LLAMAINDEX: [
                "indexing",
                "retrieval",
                "query_engine",
                "chat_engine",
                "rag_pipeline"
            ],
            AgentType.TASKWEAVER: [
                "code_first",
                "data_analytics",
                "code_execution",
                "microsoft_framework"
            ],
            # Autonomous
            AgentType.BABYAGI: [
                "task_creation",
                "task_prioritization",
                "objective_driven",
                "self_improving"
            ],
            AgentType.SUPERAGI: [
                "autonomous_agent",
                "tool_usage",
                "goal_oriented",
                "learning"
            ],
            # Local LLM
            AgentType.OLLAMA: [
                "local_llm",
                "text_generation",
                "code_generation",
                "offline_capable"
            ],
            AgentType.LOCAL_LLM: [
                "local_llm",
                "vllm",
                "tgi",
                "fast_inference"
            ],
            # Custom
            AgentType.CUSTOM: [
                "configurable",
                "api_based",
                "generic"
            ]
        }
        return capabilities.get(self.agent_type, ["generic"])


class OllamaAdapter:
    """Adapter for Ollama (local LLM)"""
    
    def __init__(self, config: Dict):
        self.base_url = config.get("url", os.getenv("OLLAMA_URL", "http://localhost:11434"))
        self.model = config.get("model", os.getenv("OLLAMA_MODEL", "llama2"))
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60)
    
    async def execute(self, instructions: str, context: Dict = None) -> Dict:
        try:
            response = await self.client.post("/api/generate", json={
                "model": self.model,
                "prompt": instructions,
                "stream": False
            })
            data = response.json()
            return {
                "status": "success",
                "output": data.get("response"),
                "model": self.model
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_status(self, execution_id: str) -> Dict:
        return {"status": "completed"}  # Ollama is synchronous
    
    async def close(self):
        await self.client.aclose()


class CustomAgentAdapter:
    """Adapter for custom agents with HTTP API"""
    
    def __init__(self, config: Dict):
        self.url = config.get("url", "http://localhost:9999")
        self.api_key = config.get("api_key", "")
        self.client = httpx.AsyncClient(
            base_url=self.url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
    
    async def execute(self, instructions: str, context: Dict = None) -> Dict:
        try:
            response = await self.client.post("/execute", json={
                "instructions": instructions,
                "context": context or {}
            })
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_status(self, execution_id: str) -> Dict:
        try:
            response = await self.client.get(f"/status/{execution_id}")
            return response.json()
        except:
            return {"status": "unknown"}
    
    async def close(self):
        await self.client.aclose()
