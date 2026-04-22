"""LangChain Adapter for FleetOps

Integration with LangChain framework
LangChain chains, agents, and tools for complex workflows

Usage:
    1. Set LANGCHAIN_API_URL or use LangServe
    2. Define chains and agents
    3. FleetOps governs chain execution
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

class LangChainAdapter:
    """FleetOps adapter for LangChain
    
    LangChain features:
    - Chains: Sequential processing pipelines
    - Agents: LLM-powered agents with tools
    - Tools: External function integrations
    - Memory: Conversation history
    - RAG: Retrieval Augmented Generation
    
    FleetOps integration:
    - Execute chains with human oversight
    - Approve agent tool usage
    - Monitor chain progress
    """
    
    def __init__(self):
        self.base_url = os.getenv("LANGCHAIN_URL", "http://localhost:8003").rstrip("/")
        self.api_key = os.getenv("LANGCHAIN_API_KEY", "")
        self.timeout = int(os.getenv("LANGCHAIN_TIMEOUT", "300"))
        
        headers = {
            "Content-Type": "application/json",
            "X-FleetOps-Source": "fleetops"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True
        )
    
    async def execute_chain(self, chain_id: str, inputs: Dict,
                           task_id: str,
                           require_tool_approval: bool = True) -> Dict[str, Any]:
        """Execute a LangChain chain"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "chain_id": chain_id,
                "inputs": inputs,
                "governance": {
                    "require_tool_approval": require_tool_approval,
                    "record_steps": True
                }
            }
            
            response = await self.client.post("/chains/invoke", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "execution_id": data.get("run_id"),
                "output": data.get("output"),
                "intermediate_steps": data.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def execute_agent(self, agent_id: str, query: str,
                           task_id: str,
                           require_tool_approval: bool = True) -> Dict[str, Any]:
        """Execute a LangChain agent with tool governance"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "agent_id": agent_id,
                "input": query,
                "governance": {
                    "require_tool_approval": require_tool_approval,
                    "record_tool_calls": True,
                    "max_iterations": 15
                }
            }
            
            response = await self.client.post("/agents/invoke", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "execution_id": data.get("run_id"),
                "output": data.get("output"),
                "tool_calls": data.get("tool_calls", []),
                "thought_process": data.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_chain_status(self, run_id: str) -> Dict[str, Any]:
        """Get chain execution status"""
        try:
            response = await self.client.get(f"/runs/{run_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def approve_tool_call(self, run_id: str, tool_call_id: str,
                               approved: bool = True,
                               comments: Optional[str] = None) -> Dict[str, Any]:
        """Approve or reject a tool call in an agent execution"""
        try:
            payload = {
                "tool_call_id": tool_call_id,
                "approved": approved,
                "comments": comments or ""
            }
            
            response = await self.client.post(
                f"/runs/{run_id}/tools/{tool_call_id}/approve",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_available_chains(self) -> List[Dict]:
        """Get list of available chains"""
        try:
            response = await self.client.get("/chains")
            return response.json().get("chains", [])
        except:
            return []
    
    async def get_available_agents(self) -> List[Dict]:
        """Get list of available agents"""
        try:
            response = await self.client.get("/agents")
            return response.json().get("agents", [])
        except:
            return []
    
    async def close(self):
        await self.client.aclose()

langchain_adapter = LangChainAdapter()


class LlamaIndexAdapter:
    """FleetOps adapter for LlamaIndex (GPT Index)
    
    LlamaIndex specializes in:
    - Data indexing and retrieval
    - Query engines
    - Chat engines
    - RAG pipelines
    """
    
    def __init__(self):
        self.base_url = os.getenv("LLAMAINDEX_URL", "http://localhost:8004").rstrip("/")
        self.api_key = os.getenv("LLAMAINDEX_API_KEY", "")
        self.timeout = int(os.getenv("LLAMAINDEX_TIMEOUT", "300"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def query_index(self, index_id: str, query: str,
                         task_id: str) -> Dict[str, Any]:
        """Query an indexed knowledge base"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "index_id": index_id,
                "query": query
            }
            
            response = await self.client.post("/query", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "response": data.get("response"),
                "source_nodes": data.get("source_nodes", []),
                "metadata": data.get("metadata", {})
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def chat_with_index(self, index_id: str, message: str,
                             conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with an indexed knowledge base"""
        try:
            payload = {
                "index_id": index_id,
                "message": message,
                "conversation_id": conversation_id
            }
            
            response = await self.client.post("/chat", json=payload)
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_indices(self) -> List[Dict]:
        """List available indices"""
        try:
            response = await self.client.get("/indices")
            return response.json().get("indices", [])
        except:
            return []
    
    async def close(self):
        await self.client.aclose()

llamaindex_adapter = LlamaIndexAdapter()


class BabyAGIAdapter:
    """FleetOps adapter for BabyAGI / BabyBeeAGI
    
    Task-driven autonomous agent that:
    1. Creates tasks based on objective
    2. Prioritizes tasks
    3. Executes tasks
    4. Creates new tasks based on results
    """
    
    def __init__(self):
        self.base_url = os.getenv("BABYAGI_URL", "http://localhost:8005").rstrip("/")
        self.api_key = os.getenv("BABYAGI_API_KEY", "")
        self.timeout = int(os.getenv("BABYAGI_TIMEOUT", "300"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def start_objective(self, objective: str, task_id: str,
                            first_task: str = "",
                            max_iterations: int = 10) -> Dict[str, Any]:
        """Start BabyAGI with an objective"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "objective": objective,
                "first_task": first_task or f"Develop a task list for: {objective}",
                "max_iterations": max_iterations,
                "governance": {
                    "require_task_approval": True,
                    "max_auto_tasks": 3
                }
            }
            
            response = await self.client.post("/run", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "started",
                "run_id": data.get("run_id"),
                "task_count": data.get("task_count", 0)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get BabyAGI run status"""
        try:
            response = await self.client.get(f"/runs/{run_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def approve_task(self, run_id: str, task_id: str,
                          approved: bool = True) -> Dict[str, Any]:
        """Approve a task in BabyAGI"""
        try:
            payload = {
                "task_id": task_id,
                "approved": approved
            }
            
            response = await self.client.post(
                f"/runs/{run_id}/tasks/{task_id}/approve",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

babyagi_adapter = BabyAGIAdapter()


class MetaGPTAdapter:
    """FleetOps adapter for MetaGPT
    
    MetaGPT simulates a software company with:
    - Product Manager
    - Architect
    - Project Manager
    - Engineer
    - QA Engineer
    
    Each role is an agent that collaborates.
    """
    
    def __init__(self):
        self.base_url = os.getenv("METAGPT_URL", "http://localhost:8006").rstrip("/")
        self.api_key = os.getenv("METAGPT_API_KEY", "")
        self.timeout = int(os.getenv("METAGPT_TIMEOUT", "600"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def start_project(self, idea: str, task_id: str,
                           investment: float = 3.0,
                           n_round: int = 5) -> Dict[str, Any]:
        """Start a MetaGPT software project"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "idea": idea,
                "investment": investment,
                "n_round": n_round,
                "governance": {
                    "require_design_approval": True,
                    "require_code_approval": True
                }
            }
            
            response = await self.client.post("/projects", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "started",
                "project_id": data.get("id"),
                "roles": data.get("roles", [])
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get MetaGPT project status"""
        try:
            response = await self.client.get(f"/projects/{project_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def approve_deliverable(self, project_id: str,
                                 deliverable_type: str,  # design, code, test
                                 approved: bool = True,
                                 comments: Optional[str] = None) -> Dict[str, Any]:
        """Approve a MetaGPT deliverable"""
        try:
            payload = {
                "deliverable_type": deliverable_type,
                "approved": approved,
                "comments": comments or ""
            }
            
            response = await self.client.post(
                f"/projects/{project_id}/approve",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

metagpt_adapter = MetaGPTAdapter()


class ChatDevAdapter:
    """FleetOps adapter for ChatDev
    
    ChatDev simulates a software development team
    with chat-based collaboration.
    """
    
    def __init__(self):
        self.base_url = os.getenv("CHATDEV_URL", "http://localhost:8007").rstrip("/")
        self.api_key = os.getenv("CHATDEV_API_KEY", "")
        self.timeout = int(os.getenv("CHATDEV_TIMEOUT", "600"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def start_chat(self, task_id: str, task: str,
                        organization: str = "DefaultOrganization",
                        config_phase: str = "Default",
                        config_chain: str = "Default") -> Dict[str, Any]:
        """Start a ChatDev session"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "task": task,
                "organization": organization,
                "config_phase": config_phase,
                "config_chain": config_chain,
                "governance": {
                    "require_phase_approval": True
                }
            }
            
            response = await self.client.post("/chat", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "started",
                "chat_id": data.get("id"),
                "phases": data.get("phases", [])
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_chat_status(self, chat_id: str) -> Dict[str, Any]:
        """Get ChatDev session status"""
        try:
            response = await self.client.get(f"/chat/{chat_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def approve_phase(self, chat_id: str, phase: str,
                           approved: bool = True) -> Dict[str, Any]:
        """Approve a ChatDev phase"""
        try:
            payload = {
                "phase": phase,
                "approved": approved
            }
            
            response = await self.client.post(
                f"/chat/{chat_id}/phases/{phase}/approve",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

chatdev_adapter = ChatDevAdapter()


class GPTeamAdapter:
    """FleetOps adapter for GPTeam
    
    GPTeam uses hierarchical agent teams for complex tasks.
    """
    
    def __init__(self):
        self.base_url = os.getenv("GPTEAM_URL", "http://localhost:8008").rstrip("/")
        self.api_key = os.getenv("GPTEAM_API_KEY", "")
        self.timeout = int(os.getenv("GPTEAM_TIMEOUT", "600"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def create_team(self, name: str, hierarchy: List[Dict]) -> Dict[str, Any]:
        """Create a hierarchical agent team"""
        try:
            payload = {
                "name": name,
                "hierarchy": hierarchy
            }
            
            response = await self.client.post("/teams", json=payload)
            response.raise_for_status()
            
            return {
                "status": "created",
                "team_id": response.json().get("id")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def assign_task(self, team_id: str, task_id: str,
                         task: str) -> Dict[str, Any]:
        """Assign task to a team"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "task": task
            }
            
            response = await self.client.post(
                f"/teams/{team_id}/tasks",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

gpteam_adapter = GPTeamAdapter()


class AgentVerseAdapter:
    """FleetOps adapter for AgentVerse
    
    Multi-agent environment for collaborative problem-solving.
    """
    
    def __init__(self):
        self.base_url = os.getenv("AGENTVERSE_URL", "http://localhost:8009").rstrip("/")
        self.api_key = os.getenv("AGENTVERSE_API_KEY", "")
        self.timeout = int(os.getenv("AGENTVERSE_TIMEOUT", "300"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def create_environment(self, name: str, agents: List[Dict],
                                task_description: str) -> Dict[str, Any]:
        """Create a multi-agent environment"""
        try:
            payload = {
                "name": name,
                "agents": agents,
                "task_description": task_description
            }
            
            response = await self.client.post("/environments", json=payload)
            response.raise_for_status()
            
            return {
                "status": "created",
                "env_id": response.json().get("id")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run_simulation(self, env_id: str, task_id: str) -> Dict[str, Any]:
        """Run a multi-agent simulation"""
        try:
            payload = {"fleetops_task_id": task_id}
            
            response = await self.client.post(
                f"/environments/{env_id}/run",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

agentverse_adapter = AgentVerseAdapter()


class SuperAGIAdapter:
    """FleetOps adapter for SuperAGI
    
    Open-source autonomous AI agent framework.
    """
    
    def __init__(self):
        self.base_url = os.getenv("SUPERAGI_URL", "http://localhost:8010").rstrip("/")
        self.api_key = os.getenv("SUPERAGI_API_KEY", "")
        self.timeout = int(os.getenv("SUPERAGI_TIMEOUT", "600"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def create_agent(self, name: str, description: str,
                          goals: List[str], tools: List[str]) -> Dict[str, Any]:
        """Create a SuperAGI agent"""
        try:
            payload = {
                "name": name,
                "description": description,
                "goal": goals,
                "tools": tools
            }
            
            response = await self.client.post("/agents", json=payload)
            response.raise_for_status()
            
            return {
                "status": "created",
                "agent_id": response.json().get("id")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run_agent(self, agent_id: str, task_id: str,
                       prompt: str) -> Dict[str, Any]:
        """Run a SuperAGI agent"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "prompt": prompt
            }
            
            response = await self.client.post(
                f"/agents/{agent_id}/run",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get SuperAGI agent status"""
        try:
            response = await self.client.get(f"/agents/{agent_id}")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

superagi_adapter = SuperAGIAdapter()


class PraisonAIAdapter:
    """FleetOps adapter for PraisonAI
    
    Multi-agent framework with auto-generated agents.
    """
    
    def __init__(self):
        self.base_url = os.getenv("PRAISONAI_URL", "http://localhost:8011").rstrip("/")
        self.api_key = os.getenv("PRAISONAI_API_KEY", "")
        self.timeout = int(os.getenv("PRAISONAI_TIMEOUT", "300"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def create_crew(self, topic: str, roles: List[str]) -> Dict[str, Any]:
        """Create a PraisonAI crew with auto-generated agents"""
        try:
            payload = {
                "topic": topic,
                "roles": roles
            }
            
            response = await self.client.post("/crews", json=payload)
            response.raise_for_status()
            
            return {
                "status": "created",
                "crew_id": response.json().get("id"),
                "agents": response.json().get("agents", [])
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run_crew(self, crew_id: str, task_id: str) -> Dict[str, Any]:
        """Run a PraisonAI crew"""
        try:
            payload = {"fleetops_task_id": task_id}
            
            response = await self.client.post(
                f"/crews/{crew_id}/run",
                json=payload
            )
            return response.json()
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

praisonai_adapter = PraisonAIAdapter()


class TaskWeaverAdapter:
    """FleetOps adapter for TaskWeaver (Microsoft)
    
    Code-first agent framework for data analytics.
    """
    
    def __init__(self):
        self.base_url = os.getenv("TASKWEAVER_URL", "http://localhost:8012").rstrip("/")
        self.api_key = os.getenv("TASKWEAVER_API_KEY", "")
        self.timeout = int(os.getenv("TASKWEAVER_TIMEOUT", "300"))
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def send_request(self, task_id: str, query: str) -> Dict[str, Any]:
        """Send a request to TaskWeaver"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "query": query
            }
            
            response = await self.client.post("/sessions", json=payload)
            response.raise_for_status()
            
            return {
                "status": "success",
                "session_id": response.json().get("id"),
                "response": response.json().get("response")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

taskweaver_adapter = TaskWeaverAdapter()


class LocalLLMAdapter:
    """Generic adapter for local LLMs (vLLM, TGI, etc.)"""
    
    def __init__(self):
        self.base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:8013").rstrip("/")
        self.model = os.getenv("LOCAL_LLM_MODEL", "")
        self.timeout = int(os.getenv("LOCAL_LLM_TIMEOUT", "120"))
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def generate(self, prompt: str, task_id: str,
                      max_tokens: int = 1024,
                      temperature: float = 0.7) -> Dict[str, Any]:
        """Generate text with local LLM"""
        try:
            payload = {
                "fleetops_task_id": task_id,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            if self.model:
                payload["model"] = self.model
            
            response = await self.client.post("/generate", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "text": data.get("text") or data.get("generated_text"),
                "model": self.model or data.get("model", "unknown")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

local_llm_adapter = LocalLLMAdapter()


# ═══════════════════════════════════════
# UNIFIED ADAPTER REGISTRY
# ═══════════════════════════════════════

ALL_ADAPTERS = {
    "claude_code": {
        "name": "Claude Code",
        "category": "ide",
        "adapter": "ide_agent_adapter",
        "supports_governance": True,
        "url_env": "CLAUDE_CODE_CLI",
        "description": "Anthropic's CLI-based AI assistant for file editing"
    },
    "copilot": {
        "name": "GitHub Copilot",
        "category": "ide",
        "adapter": "ide_agent_adapter",
        "supports_governance": True,
        "url_env": "GITHUB_TOKEN",
        "description": "GitHub's AI pair programmer for code suggestions"
    },
    "cursor": {
        "name": "Cursor",
        "category": "ide",
        "adapter": "ide_agent_adapter",
        "supports_governance": True,
        "url_env": "CURSOR_API_URL",
        "description": "AI-powered IDE with Composer and Agent mode"
    },
    "aider": {
        "name": "Aider",
        "category": "ide",
        "adapter": "ide_agent_adapter",
        "supports_governance": True,
        "url_env": "AIDER_CLI",
        "description": "CLI pair programming with multiple LLMs"
    },
    "devin": {
        "name": "Devin",
        "category": "ide",
        "adapter": "ide_agent_adapter",
        "supports_governance": True,
        "url_env": "DEVIN_API_KEY",
        "description": "Autonomous AI software engineer from Cognition"
    },
    "cody": {
        "name": "Cody",
        "category": "ide",
        "adapter": "ide_agent_adapter",
        "supports_governance": False,
        "url_env": "CODY_API_KEY",
        "description": "Sourcegraph's AI code intelligence"
    },
    "openclaw": {
        "name": "OpenClaw",
        "category": "personal",
        "adapter": "openclaw_adapter",
        "supports_governance": True,
        "url_env": "OPENCLAW_URL",
        "description": "Session-based autonomous agent"
    },
    "hermes": {
        "name": "Hermes",
        "category": "personal",
        "adapter": "hermes_adapter",
        "supports_governance": True,
        "url_env": "HERMES_URL",
        "description": "Task-based personal assistant"
    },
    "crewai": {
        "name": "CrewAI",
        "category": "multi-agent",
        "adapter": "crewai_adapter",
        "supports_governance": True,
        "url_env": "CREWAI_URL",
        "description": "Multi-agent crew orchestration"
    },
    "autogen": {
        "name": "AutoGen",
        "category": "multi-agent",
        "adapter": "autogen_adapter",
        "supports_governance": True,
        "url_env": "AUTOGEN_URL",
        "description": "Microsoft multi-agent conversations"
    },
    "langchain": {
        "name": "LangChain",
        "category": "framework",
        "adapter": "langchain_adapter",
        "supports_governance": True,
        "url_env": "LANGCHAIN_URL",
        "description": "Chains and agents framework"
    },
    "llamaindex": {
        "name": "LlamaIndex",
        "category": "framework",
        "adapter": "llamaindex_adapter",
        "supports_governance": False,
        "url_env": "LLAMAINDEX_URL",
        "description": "Data indexing and RAG"
    },
    "ollama": {
        "name": "Ollama",
        "category": "local-llm",
        "adapter": "ollama_adapter",
        "supports_governance": False,
        "url_env": "OLLAMA_URL",
        "description": "Local LLM runner"
    },
    "babyagi": {
        "name": "BabyAGI",
        "category": "autonomous",
        "adapter": "babyagi_adapter",
        "supports_governance": True,
        "url_env": "BABYAGI_URL",
        "description": "Task-driven autonomous agent"
    },
    "metagpt": {
        "name": "MetaGPT",
        "category": "multi-agent",
        "adapter": "metagpt_adapter",
        "supports_governance": True,
        "url_env": "METAGPT_URL",
        "description": "Software company simulation"
    },
    "chatdev": {
        "name": "ChatDev",
        "category": "multi-agent",
        "adapter": "chatdev_adapter",
        "supports_governance": True,
        "url_env": "CHATDEV_URL",
        "description": "Chat-based dev team"
    },
    "gpteam": {
        "name": "GPTeam",
        "category": "multi-agent",
        "adapter": "gpteam_adapter",
        "supports_governance": True,
        "url_env": "GPTEAM_URL",
        "description": "Hierarchical agent teams"
    },
    "agentverse": {
        "name": "AgentVerse",
        "category": "multi-agent",
        "adapter": "agentverse_adapter",
        "supports_governance": True,
        "url_env": "AGENTVERSE_URL",
        "description": "Multi-agent environments"
    },
    "superagi": {
        "name": "SuperAGI",
        "category": "autonomous",
        "adapter": "superagi_adapter",
        "supports_governance": True,
        "url_env": "SUPERAGI_URL",
        "description": "Open-source autonomous AI"
    },
    "praisonai": {
        "name": "PraisonAI",
        "category": "multi-agent",
        "adapter": "praisonai_adapter",
        "supports_governance": True,
        "url_env": "PRAISONAI_URL",
        "description": "Auto-generated agent crews"
    },
    "taskweaver": {
        "name": "TaskWeaver",
        "category": "framework",
        "adapter": "taskweaver_adapter",
        "supports_governance": True,
        "url_env": "TASKWEAVER_URL",
        "description": "Microsoft code-first analytics"
    },
    "local_llm": {
        "name": "Local LLM (vLLM/TGI)",
        "category": "local-llm",
        "adapter": "local_llm_adapter",
        "supports_governance": False,
        "url_env": "LOCAL_LLM_URL",
        "description": "Generic local LLM endpoint"
    },
    "custom": {
        "name": "Custom Agent",
        "category": "custom",
        "adapter": "custom_adapter",
        "supports_governance": True,
        "url_env": "CUSTOM_AGENT_URL",
        "description": "Any HTTP API agent"
    }
}

def get_adapter_info(agent_type: str) -> Dict[str, Any]:
    """Get adapter info for an agent type"""
    return ALL_ADAPTERS.get(agent_type, ALL_ADAPTERS["custom"])

def list_all_adapters() -> List[Dict[str, Any]]:
    """List all available adapters"""
    return [
        {
            "id": key,
            **value
        }
        for key, value in ALL_ADAPTERS.items()
    ]

def get_adapters_by_category(category: str) -> List[Dict[str, Any]]:
    """Get adapters by category"""
    return [
        {
            "id": key,
            **value
        }
        for key, value in ALL_ADAPTERS.items()
        if value["category"] == category
    ]

# Categories
ADAPTER_CATEGORIES = {
    "ide": "IDE Agents (Claude Code, Copilot, Cursor, Aider, Devin, Cody)",
    "personal": "Personal AI Assistants (OpenClaw, Hermes)",
    "multi-agent": "Multi-Agent Frameworks (CrewAI, AutoGen, MetaGPT, ChatDev, GPTeam, AgentVerse, PraisonAI)",
    "framework": "Agent Frameworks (LangChain, LlamaIndex, TaskWeaver)",
    "autonomous": "Autonomous Agents (BabyAGI, SuperAGI)",
    "local-llm": "Local LLMs (Ollama, vLLM, TGI)",
    "custom": "Custom Integrations"
}
