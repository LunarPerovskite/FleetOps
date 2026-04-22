"""Ollama Adapter for FleetOps

Supports BOTH local and cloud Ollama:
- Local: http://localhost:11434 (your machine)
- Cloud: https://ollama.com/api (hosted) or any remote URL

Tracks costs:
- Local: electricity + hardware amortization
- Cloud: per-request or subscription pricing
"""

import os
from typing import Dict, Any, Optional, List
import httpx

from app.core.cost_tracking import cost_tracker

class OllamaAdapter:
    """FleetOps adapter for Ollama
    
    Ollama can run:
    - Locally: docker run ollama/ollama
    - On a VPS: your own server
    - Cloud: ollama.com (coming soon) or any hosted instance
    """
    
    def __init__(self):
        # Can be any URL: local, VPS, cloud
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.default_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        # Is this local or cloud?
        self.is_local = "localhost" in self.base_url or "127.0.0.1" in self.base_url
        self.is_cloud = not self.is_local
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama is running"""
        try:
            response = await self.client.get("/api/tags")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": self.base_url,
                "is_local": self.is_local,
                "is_cloud": self.is_cloud
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e),
                "url": self.base_url
            }
    
    async def list_models(self) -> List[Dict]:
        """List available models"""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": model.get("name"),
                    "name": model.get("name"),
                    "size": model.get("size"),
                    "parameter_size": model.get("details", {}).get("parameter_size"),
                    "quantization": model.get("details", {}).get("quantization_level"),
                    "modified": model.get("modified_at"),
                    "digest": model.get("digest")
                }
                for model in data.get("models", [])
            ]
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull/download a model"""
        try:
            response = await self.client.post("/api/pull", json={
                "name": model_name,
                "stream": False
            })
            response.raise_for_status()
            
            return {
                "status": "success",
                "model": model_name,
                "message": f"Pulled {model_name}"
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def generate(self, prompt: str, task_id: str,
                      model: Optional[str] = None,
                      system: Optional[str] = None,
                      user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate text with Ollama
        
        For local: estimates electricity cost
        For cloud: tracks actual usage
        """
        try:
            model = model or self.default_model
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if system:
                payload["system"] = system
            
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Ollama doesn't return token usage, estimate from text
            output_text = data.get("response", "")
            estimated_output = len(output_text) // 4  # ~4 chars per token
            input_tokens = len(prompt) // 4
            
            # Track cost based on local vs cloud
            if self.is_local:
                # Local: estimate electricity cost
                cost_result = await cost_tracker.track_local_compute(
                    service="ollama",
                    model=model,
                    agent_id="ollama_adapter",
                    task_id=task_id,
                    compute_seconds=2.0,  # rough estimate
                    hardware_type=os.getenv("OLLAMA_HARDWARE", "gpu_rtx4090"),
                    user_id=user_id
                )
            else:
                # Cloud: use configured pricing
                cost_result = await cost_tracker.track_usage(
                    service="ollama_cloud",
                    model=model,
                    agent_id="ollama_adapter",
                    task_id=task_id,
                    user_id=user_id,
                    input_tokens=input_tokens,
                    output_tokens=estimated_output,
                    metadata={
                        "is_cloud": True,
                        "url": self.base_url,
                        "estimated": True  # Ollama doesn't return usage
                    }
                )
            
            return {
                "status": "success",
                "content": output_text,
                "model": model,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": estimated_output,
                    "estimated": True
                },
                "cost_usd": cost_result["cost_usd"],
                "is_local": self.is_local
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def chat(self, messages: List[Dict], task_id: str,
                  model: Optional[str] = None,
                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with Ollama"""
        try:
            model = model or self.default_model
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Estimate tokens
            output_text = data.get("message", {}).get("content", "")
            estimated_output = len(output_text) // 4
            input_text = " ".join([m.get("content", "") for m in messages])
            input_tokens = len(input_text) // 4
            
            # Track cost
            if self.is_local:
                cost_result = await cost_tracker.track_local_compute(
                    service="ollama",
                    model=model,
                    agent_id="ollama_adapter",
                    task_id=task_id,
                    compute_seconds=3.0,
                    hardware_type=os.getenv("OLLAMA_HARDWARE", "gpu_rtx4090"),
                    user_id=user_id
                )
            else:
                cost_result = await cost_tracker.track_usage(
                    service="ollama_cloud",
                    model=model,
                    agent_id="ollama_adapter",
                    task_id=task_id,
                    user_id=user_id,
                    input_tokens=input_tokens,
                    output_tokens=estimated_output,
                    metadata={
                        "is_cloud": True,
                        "url": self.base_url,
                        "estimated": True
                    }
                )
            
            return {
                "status": "success",
                "content": output_text,
                "model": model,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": estimated_output,
                    "estimated": True
                },
                "cost_usd": cost_result["cost_usd"],
                "is_local": self.is_local
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# Singleton
ollama_adapter = OllamaAdapter()
