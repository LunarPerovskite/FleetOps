"""OpenWebUI Adapter for FleetOps

Connects FleetOps to OpenWebUI instance for:
- Chat interface access
- Model management
- Conversation history
- Cost tracking
- Governance
"""

import os
from typing import Dict, Any, Optional, List
import httpx

from app.core.usage_extraction import RealUsageExtractor
from app.core.cost_tracking import cost_tracker

class OpenWebUIAdapter:
    """FleetOps adapter for OpenWebUI
    
    OpenWebUI exposes these APIs:
    - GET  /api/models           - List models
    - POST /api/chat/completions - Chat
    - GET  /api/chats             - Conversation history
    - POST /api/tasks             - Background tasks
    
    FleetOps adds:
    - Cost tracking
    - Budget enforcement
    - Model approval
    - Usage limits
    """
    
    def __init__(self):
        self.base_url = os.getenv("OPENWEBUI_URL", "http://localhost:8080").rstrip("/")
        self.api_key = os.getenv("OPENWEBUI_API_KEY", "")
        self.timeout = int(os.getenv("OPENWEBUI_TIMEOUT", "120"))
        self.default_model = os.getenv("OPENWEBUI_DEFAULT_MODEL", "llama3.1:8b")
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if OpenWebUI is running"""
        try:
            response = await self.client.get("/health")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": self.base_url,
                "version": response.headers.get("X-OpenWebUI-Version", "unknown")
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e),
                "url": self.base_url
            }
    
    async def list_models(self) -> List[Dict]:
        """List all models available in OpenWebUI"""
        try:
            response = await self.client.get("/api/models")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("data", []):
                models.append({
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "object": model.get("object"),
                    "created": model.get("created"),
                    "owned_by": model.get("owned_by"),
                    # Ollama-specific info
                    "size": model.get("size", "unknown"),
                    "format": model.get("format", "unknown"),
                    "parameter_count": model.get("details", {}).get("parameter_size"),
                    "quantization": model.get("details", {}).get("quantization_level"),
                })
            
            return models
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull/download a model into Ollama via OpenWebUI"""
        try:
            response = await self.client.post("/api/models/pull", json={
                "name": model_name
            })
            response.raise_for_status()
            
            return {
                "status": "pulling",
                "model": model_name,
                "message": f"Started pulling {model_name}"
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def chat(self, message: str, task_id: str,
                  model: Optional[str] = None,
                  system_prompt: Optional[str] = None,
                  user_id: Optional[str] = None,
                  stream: bool = False) -> Dict[str, Any]:
        """Chat through OpenWebUI with FleetOps governance
        
        Flow:
        1. Check if model is allowed
        2. Estimate cost
        3. Check budget
        4. Send request
        5. Extract real usage
        6. Track cost
        7. Return response
        """
        try:
            model = model or self.default_model
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            # Send to OpenWebUI
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2048
                }
            }
            
            response = await self.client.post("/api/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract real usage from response
            usage = self._extract_usage(data)
            
            # Track cost with real usage
            cost_result = await cost_tracker.track_usage(
                service="openwebui",
                model=model,
                agent_id="openwebui_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                metadata={
                    "has_real_usage": usage["has_real_usage"],
                    "response_time_ms": usage.get("response_time_ms"),
                    "source": "openwebui"
                }
            )
            
            return {
                "status": "success",
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model", model),
                "usage": usage,
                "cost_usd": cost_result["cost_usd"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def chat_with_history(self, messages: List[Dict], task_id: str,
                               model: Optional[str] = None,
                               user_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with conversation history (multi-turn)"""
        try:
            model = model or self.default_model
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            response = await self.client.post("/api/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract usage
            usage = self._extract_usage(data)
            
            # Track cost
            cost_result = await cost_tracker.track_usage(
                service="openwebui",
                model=model,
                agent_id="openwebui_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"]
            )
            
            return {
                "status": "success",
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model", model),
                "usage": usage,
                "cost_usd": cost_result["cost_usd"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_conversations(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get chat conversation history"""
        try:
            params = {}
            if user_id:
                params["user_id"] = user_id
            
            response = await self.client.get("/api/chats", params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def get_conversation(self, chat_id: str) -> Dict:
        """Get a specific conversation"""
        try:
            response = await self.client.get(f"/api/chats/{chat_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_title(self, message: str, model: Optional[str] = None) -> Dict:
        """Generate a title for a conversation"""
        try:
            response = await self.client.post("/api/tasks/title/generate", json={
                "model": model or self.default_model,
                "prompt": message
            })
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_usage(self, data: Dict) -> Dict:
        """Extract usage data from OpenWebUI response
        
        OpenWebUI returns OpenAI-compatible format:
        {
            "usage": {
                "prompt_tokens": 123,
                "completion_tokens": 456,
                "total_tokens": 579
            }
        }
        
        But for Ollama, it may not include usage.
        We handle both cases.
        """
        usage = data.get("usage", {})
        
        if usage:
            # OpenAI-compatible response with usage
            return {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "has_real_usage": True
            }
        else:
            # Ollama response without usage - estimate
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            estimated_output = len(content) // 4
            
            return {
                "input_tokens": 0,  # Can't know without counting
                "output_tokens": estimated_output,
                "total_tokens": estimated_output,
                "has_real_usage": False,
                "estimated": True
            }
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
openwebui_adapter = OpenWebUIAdapter()
