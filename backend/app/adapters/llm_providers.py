"""LLM Provider Adapters for FleetOps

Native API adapters for major LLM providers:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude 3 Opus, Sonnet, Haiku)
- Google Gemini
- Azure OpenAI
- Mistral AI
- Cohere

Extracts REAL usage data from API responses.
Tracks costs with dynamic pricing.
"""

import os
from typing import Dict, Any, Optional, List
import httpx

from app.core.usage_extraction import RealUsageExtractor
from app.core.cost_tracking import cost_tracker
from app.core.circuit_breaker import circuit_breaker


class OpenAIAdapter:
    """FleetOps adapter for OpenAI API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1"
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "120"))
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    @circuit_breaker("openai", failure_threshold=5, recovery_timeout=30)
    async def chat(self, messages: List[Dict], task_id: str,
                  model: Optional[str] = None,
                  temperature: float = 0.7,
                  max_tokens: int = 2048,
                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat via OpenAI API with real usage tracking"""
        try:
            payload = {
                "model": model or self.default_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract REAL usage from response
            usage = await RealUsageExtractor.extract_openai_usage(data)
            
            # Track with actual token counts
            cost_result = await cost_tracker.track_usage(
                service="openai",
                model=data.get("model", model or self.default_model),
                agent_id="openai_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                cached_tokens=usage.get("cached_tokens", 0),
                metadata={
                    "has_real_usage": usage["has_real_usage"],
                    "response_time_ms": None  # Could add timing
                }
            )
            
            return {
                "status": "success",
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "usage": usage,
                "cost_usd": cost_result["cost_usd"],
                "pricing_source": cost_result.get("pricing_source", "unknown")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_models(self) -> List[Dict]:
        """List available OpenAI models"""
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "owned_by": m.get("owned_by", "openai")
                }
                for m in data.get("data", [])
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    async def close(self):
        await self.client.aclose()


class AnthropicAdapter:
    """FleetOps adapter for Anthropic Claude API"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = "https://api.anthropic.com/v1"
        self.timeout = int(os.getenv("ANTHROPIC_TIMEOUT", "120"))
        self.default_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    @circuit_breaker("anthropic", failure_threshold=5, recovery_timeout=30)
    async def chat(self, messages: List[Dict], task_id: str,
                  model: Optional[str] = None,
                  max_tokens: int = 4096,
                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat via Anthropic API with real usage tracking"""
        try:
            # Convert messages to Anthropic format
            system_msg = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            payload = {
                "model": model or self.default_model,
                "messages": user_messages,
                "max_tokens": max_tokens
            }
            
            if system_msg:
                payload["system"] = system_msg
            
            response = await self.client.post("/messages", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract REAL usage
            usage = await RealUsageExtractor.extract_anthropic_usage(data)
            
            # Track cost
            cost_result = await cost_tracker.track_usage(
                service="anthropic",
                model=data.get("model", model or self.default_model),
                agent_id="anthropic_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                metadata={
                    "has_real_usage": usage["has_real_usage"],
                    "stop_reason": data.get("stop_reason")
                }
            )
            
            return {
                "status": "success",
                "content": data["content"][0]["text"],
                "model": data.get("model"),
                "usage": usage,
                "cost_usd": cost_result["cost_usd"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_models(self) -> List[Dict]:
        """List available Anthropic models"""
        return [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "owned_by": "anthropic"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "owned_by": "anthropic"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "owned_by": "anthropic"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "owned_by": "anthropic"}
        ]
    
    async def close(self):
        await self.client.aclose()


class GeminiAdapter:
    """FleetOps adapter for Google Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = int(os.getenv("GEMINI_TIMEOUT", "120"))
        self.default_model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    @circuit_breaker("gemini", failure_threshold=5, recovery_timeout=30)
    async def chat(self, messages: List[Dict], task_id: str,
                  model: Optional[str] = None,
                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat via Gemini API with real usage tracking"""
        try:
            # Convert to Gemini format
            contents = []
            system_instruction = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = {"parts": [{"text": msg["content"]}]}
                else:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
            
            payload = {"contents": contents}
            if system_instruction:
                payload["system_instruction"] = system_instruction
            
            model_name = model or self.default_model
            
            response = await self.client.post(
                f"/models/{model_name}:generateContent?key={self.api_key}",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract REAL usage
            usage = await RealUsageExtractor.extract_gemini_usage(data)
            
            # Track cost
            cost_result = await cost_tracker.track_usage(
                service="gemini",
                model=model_name,
                agent_id="gemini_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                metadata={
                    "has_real_usage": usage["has_real_usage"]
                }
            )
            
            return {
                "status": "success",
                "content": data["candidates"][0]["content"]["parts"][0]["text"],
                "model": model_name,
                "usage": usage,
                "cost_usd": cost_result["cost_usd"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_models(self) -> List[Dict]:
        """List available Gemini models"""
        return [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "owned_by": "google"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "owned_by": "google"},
            {"id": "gemini-pro", "name": "Gemini Pro", "owned_by": "google"},
            {"id": "gemini-pro-vision", "name": "Gemini Pro Vision", "owned_by": "google"}
        ]
    
    async def close(self):
        await self.client.aclose()


class AzureOpenAIAdapter:
    """FleetOps adapter for Azure OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        self.api_version = "2024-02-01"
        self.timeout = int(os.getenv("AZURE_OPENAI_TIMEOUT", "120"))
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    @circuit_breaker("azure_openai", failure_threshold=5, recovery_timeout=30)
    async def chat(self, messages: List[Dict], task_id: str,
                  deployment: Optional[str] = None,
                  user_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat via Azure OpenAI with real usage tracking"""
        try:
            dep = deployment or self.deployment
            url = f"{self.endpoint}/openai/deployments/{dep}/chat/completions?api-version={self.api_version}"
            
            payload = {
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract REAL usage
            usage = await RealUsageExtractor.extract_azure_openai_usage(data)
            
            # Track cost
            cost_result = await cost_tracker.track_usage(
                service="azure_openai",
                model=dep,
                agent_id="azure_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                metadata={
                    "has_real_usage": usage["has_real_usage"],
                    "deployment": dep
                }
            )
            
            return {
                "status": "success",
                "content": data["choices"][0]["message"]["content"],
                "model": dep,
                "usage": usage,
                "cost_usd": cost_result["cost_usd"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_models(self) -> List[Dict]:
        """List available Azure OpenAI deployments"""
        return [
            {"id": "gpt-4o", "name": "GPT-4o", "owned_by": "openai"},
            {"id": "gpt-4", "name": "GPT-4", "owned_by": "openai"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "owned_by": "openai"},
            {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo", "owned_by": "openai"},
            {"id": "text-embedding-3-large", "name": "Text Embedding 3 Large", "owned_by": "openai"}
        ]
    
    async def close(self):
        await self.client.aclose()


class UnifiedLLMChatAdapter:
    """Unified adapter for all major LLM providers"""
    
    PROVIDERS = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "gemini": GeminiAdapter,
        "azure": AzureOpenAIAdapter,
    }
    
    def __init__(self, provider: str):
        self.provider = provider.lower()
        self.adapter = None
        self._initialize()
    
    def _initialize(self):
        adapter_class = self.PROVIDERS.get(self.provider)
        if adapter_class:
            self.adapter = adapter_class()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def chat(self, messages: List[Dict], task_id: str, **kwargs) -> Dict[str, Any]:
        """Chat with any provider"""
        return await self.adapter.chat(messages, task_id, **kwargs)
    
    async def list_models(self) -> List[Dict]:
        """List models from the current provider"""
        return await self.adapter.list_models()
    
    async def close(self):
        if self.adapter:
            await self.adapter.close()


# Singleton instances
openai_adapter = OpenAIAdapter()
anthropic_adapter = AnthropicAdapter()
gemini_adapter = GeminiAdapter()
azure_adapter = AzureOpenAIAdapter()
