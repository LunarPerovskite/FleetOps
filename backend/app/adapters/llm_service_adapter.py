"""LLM Service Adapter for FleetOps

Integration with external LLM services and APIs:
- Perplexity (search + LLM)
- OpenRouter (unified LLM API)
- Replicate (model hosting)
- Together AI
- AnyScale
- Fireworks AI
- Groq
- Mistral AI
- Cohere
- Anthropic Claude API
- OpenAI API
- Google Gemini
- Azure OpenAI

Token & Cost Tracking:
- Tracks tokens used (input/output)
- Calculates cost per request
- Aggregates costs per agent/task
- Budget alerts and limits
"""

import os
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from decimal import Decimal
import httpx
import json

class TokenTracker:
    """Tracks token usage and costs across all LLM services"""
    
    def __init__(self):
        self.usage_log: List[Dict] = []
        self.budget_limits: Dict[str, Decimal] = {}
        self.cost_per_1k_tokens: Dict[str, Dict[str, Decimal]] = {
            "openai": {
                "gpt-4": {"input": Decimal("0.03"), "output": Decimal("0.06")},
                "gpt-4-turbo": {"input": Decimal("0.01"), "output": Decimal("0.03")},
                "gpt-3.5-turbo": {"input": Decimal("0.0005"), "output": Decimal("0.0015")},
            },
            "anthropic": {
                "claude-3-opus": {"input": Decimal("0.015"), "output": Decimal("0.075")},
                "claude-3-sonnet": {"input": Decimal("0.003"), "output": Decimal("0.015")},
                "claude-3-haiku": {"input": Decimal("0.00025"), "output": Decimal("0.00125")},
            },
            "perplexity": {
                "sonar": {"input": Decimal("0.0005"), "output": Decimal("0.0015")},
                "sonar-pro": {"input": Decimal("0.003"), "output": Decimal("0.015")},
            },
            "groq": {
                "llama3-8b": {"input": Decimal("0.0001"), "output": Decimal("0.0001")},
                "llama3-70b": {"input": Decimal("0.0006"), "output": Decimal("0.0008")},
                "mixtral-8x7b": {"input": Decimal("0.0003"), "output": Decimal("0.0005")},
            },
            "together": {
                "llama-3-70b": {"input": Decimal("0.0009"), "output": Decimal("0.0009")},
            },
            "openrouter": {
                "default": {"input": Decimal("0.001"), "output": Decimal("0.002")},
            }
        }
    
    def calculate_cost(self, service: str, model: str, 
                      input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost for a request"""
        rates = self.cost_per_1k_tokens.get(service, {}).get(model, 
                 self.cost_per_1k_tokens.get(service, {}).get("default", 
                     {"input": Decimal("0.001"), "output": Decimal("0.002")}))
        
        input_cost = (Decimal(input_tokens) / 1000) * rates["input"]
        output_cost = (Decimal(output_tokens) / 1000) * rates["output"]
        total = input_cost + output_cost
        
        return total.quantize(Decimal("0.000001"))
    
    def track_usage(self, service: str, model: str, task_id: str,
                   input_tokens: int, output_tokens: int,
                   cost: Optional[Decimal] = None) -> Dict:
        """Track token usage for a request"""
        if cost is None:
            cost = self.calculate_cost(service, model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": service,
            "model": model,
            "task_id": task_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": str(cost),
        }
        
        self.usage_log.append(entry)
        return entry
    
    def get_usage_summary(self, task_id: Optional[str] = None) -> Dict:
        """Get usage summary for a task or all"""
        entries = self.usage_log
        if task_id:
            entries = [e for e in entries if e["task_id"] == task_id]
        
        total_input = sum(e["input_tokens"] for e in entries)
        total_output = sum(e["output_tokens"] for e in entries)
        total_cost = sum(Decimal(e["cost_usd"]) for e in entries)
        
        by_service = {}
        for e in entries:
            svc = e["service"]
            if svc not in by_service:
                by_service[svc] = {"tokens": 0, "cost": Decimal("0")}
            by_service[svc]["tokens"] += e["total_tokens"]
            by_service[svc]["cost"] += Decimal(e["cost_usd"])
        
        return {
            "total_requests": len(entries),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": str(total_cost.quantize(Decimal("0.000001"))),
            "by_service": {k: {"tokens": v["tokens"], "cost": str(v["cost"])} 
                          for k, v in by_service.items()}
        }
    
    def set_budget_limit(self, task_id: str, max_cost_usd: float):
        """Set budget limit for a task"""
        self.budget_limits[task_id] = Decimal(str(max_cost_usd))
    
    def check_budget(self, task_id: str) -> Dict:
        """Check if task is within budget"""
        limit = self.budget_limits.get(task_id)
        if not limit:
            return {"has_budget": False, "remaining": None}
        
        summary = self.get_usage_summary(task_id)
        spent = Decimal(summary["total_cost_usd"])
        remaining = limit - spent
        
        return {
            "has_budget": True,
            "limit_usd": str(limit),
            "spent_usd": str(spent),
            "remaining_usd": str(remaining),
            "exceeded": remaining < 0,
            "percent_used": float((spent / limit) * 100)
        }


# Global token tracker
token_tracker = TokenTracker()


class PerplexityAdapter:
    """FleetOps adapter for Perplexity API
    
    Perplexity features:
    - Conversational search with citations
    - Real-time web search
    - Multiple models (sonar, sonar-pro, sonar-reasoning)
    """
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.base_url = "https://api.perplexity.ai"
        self.timeout = int(os.getenv("PERPLEXITY_TIMEOUT", "60"))
        self.default_model = os.getenv("PERPLEXITY_MODEL", "sonar")
        
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
    
    async def query(self, question: str, task_id: str,
                   model: Optional[str] = None,
                   search_recency: str = "month") -> Dict[str, Any]:
        """Query Perplexity with search"""
        try:
            payload = {
                "model": model or self.default_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Be precise and concise. Cite sources using [index] format."
                    },
                    {"role": "user", "content": question}
                ],
                "max_tokens": 2000,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_citations": True,
                "search_recency_filter": search_recency
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            
            # Track tokens
            cost = token_tracker.track_usage(
                service="perplexity",
                model=model or self.default_model,
                task_id=task_id,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0)
            )
            
            return {
                "status": "success",
                "answer": choice["content"],
                "citations": data.get("citations", []),
                "model": data.get("model"),
                "usage": {
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "cost_usd": cost["cost_usd"]
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


class OpenRouterAdapter:
    """FleetOps adapter for OpenRouter
    
    OpenRouter provides unified access to 100+ models:
    - OpenAI GPT-4, GPT-3.5
    - Anthropic Claude
    - Google Gemini
    - Meta Llama
    - Mistral
    - And many more
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = int(os.getenv("OPENROUTER_TIMEOUT", "120"))
        self.default_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://fleetops.local"),
            "X-Title": "FleetOps"
        }
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def chat(self, messages: List[Dict], task_id: str,
                  model: Optional[str] = None,
                  max_tokens: int = 2000,
                  temperature: float = 0.7) -> Dict[str, Any]:
        """Chat completion via OpenRouter"""
        try:
            payload = {
                "model": model or self.default_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            
            # Track tokens
            cost = token_tracker.track_usage(
                service="openrouter",
                model=model or self.default_model,
                task_id=task_id,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0)
            )
            
            return {
                "status": "success",
                "content": choice["content"],
                "model": data.get("model"),
                "provider": data.get("provider"),
                "usage": {
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "cost_usd": cost["cost_usd"]
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_models(self) -> List[Dict]:
        """List available models on OpenRouter"""
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            return response.json().get("data", [])
        except:
            return []
    
    async def close(self):
        await self.client.aclose()


class ReplicateAdapter:
    """FleetOps adapter for Replicate
    
    Replicate hosts and runs ML models:
    - LLMs (Llama, Mistral, etc.)
    - Image generation (SDXL, FLUX)
    - Audio models
    - Custom models
    """
    
    def __init__(self):
        self.api_key = os.getenv("REPLICATE_API_KEY", "")
        self.base_url = "https://api.replicate.com"
        self.timeout = int(os.getenv("REPLICATE_TIMEOUT", "300"))
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "wait"
        }
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10),
            follow_redirects=True
        )
    
    async def run_model(self, model_version: str, input_data: Dict,
                       task_id: str) -> Dict[str, Any]:
        """Run a model on Replicate"""
        try:
            payload = {
                "version": model_version,
                "input": input_data
            }
            
            response = await self.client.post("/v1/predictions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "started",
                "prediction_id": data.get("id"),
                "status_url": data.get("urls", {}).get("get"),
                "output": data.get("output")
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_prediction(self, prediction_id: str) -> Dict[str, Any]:
        """Get prediction status/result"""
        try:
            response = await self.client.get(f"/v1/predictions/{prediction_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


class GroqAdapter:
    """FleetOps adapter for Groq API
    
    Groq provides ultra-fast inference:
    - Llama 3 (8B, 70B)
    - Mixtral 8x7B
    - Gemma models
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1"
        self.timeout = int(os.getenv("GROQ_TIMEOUT", "60"))
        self.default_model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        
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
    
    async def chat(self, messages: List[Dict], task_id: str,
                  model: Optional[str] = None) -> Dict[str, Any]:
        """Chat via Groq"""
        try:
            payload = {
                "model": model or self.default_model,
                "messages": messages,
                "max_tokens": 4096
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            
            # Track tokens
            cost = token_tracker.track_usage(
                service="groq",
                model=model or self.default_model,
                task_id=task_id,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0)
            )
            
            return {
                "status": "success",
                "content": choice["content"],
                "model": data.get("model"),
                "usage": {
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "cost_usd": cost["cost_usd"]
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


class TogetherAIAdapter:
    """FleetOps adapter for Together AI"""
    
    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY", "")
        self.base_url = "https://api.together.xyz/v1"
        self.timeout = int(os.getenv("TOGETHER_TIMEOUT", "120"))
        
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
    
    async def chat(self, messages: List[Dict], task_id: str,
                  model: str = "meta-llama/Llama-3-70b-chat-hf") -> Dict[str, Any]:
        """Chat via Together AI"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 4096
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            
            cost = token_tracker.track_usage(
                service="together",
                model=model,
                task_id=task_id,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0)
            )
            
            return {
                "status": "success",
                "content": choice["content"],
                "usage": {
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "cost_usd": cost["cost_usd"]
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


class UnifiedLLMAdapter:
    """Unified adapter for all LLM services
    
    Provides single interface for:
    - Perplexity
    - OpenRouter
    - Replicate
    - Groq
    - Together AI
    - And more
    """
    
    def __init__(self, service: str):
        self.service = service.lower()
        self._adapter = None
        self._initialize()
    
    def _initialize(self):
        if self.service == "perplexity":
            self._adapter = PerplexityAdapter()
        elif self.service == "openrouter":
            self._adapter = OpenRouterAdapter()
        elif self.service == "replicate":
            self._adapter = ReplicateAdapter()
        elif self.service == "groq":
            self._adapter = GroqAdapter()
        elif self.service == "together":
            self._adapter = TogetherAIAdapter()
        else:
            raise ValueError(f"Unsupported LLM service: {self.service}")
    
    async def chat(self, messages: List[Dict], task_id: str, **kwargs) -> Dict[str, Any]:
        """Chat with any supported LLM service"""
        if self.service in ["openrouter", "groq", "together"]:
            return await self._adapter.chat(messages, task_id, **kwargs)
        elif self.service == "perplexity":
            question = messages[-1].get("content", "") if messages else ""
            return await self._adapter.query(question, task_id, **kwargs)
        else:
            return {"status": "error", "error": f"Chat not supported for {self.service}"}
    
    async def get_usage(self, task_id: str) -> Dict:
        """Get usage summary for a task"""
        return token_tracker.get_usage_summary(task_id)
    
    async def close(self):
        if hasattr(self._adapter, 'close'):
            await self._adapter.close()


# ═══════════════════════════════════════
# ADAPTER REGISTRY
# ═══════════════════════════════════════

LLM_SERVICES = {
    "perplexity": {
        "name": "Perplexity",
        "type": "search_llm",
        "adapter": "llm_service_adapter",
        "description": "Conversational search with real-time web access",
        "models": ["sonar", "sonar-pro", "sonar-reasoning"],
        "features": ["web_search", "citations", "real_time"]
    },
    "openrouter": {
        "name": "OpenRouter",
        "type": "aggregator",
        "adapter": "llm_service_adapter",
        "description": "Unified API for 100+ models",
        "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "meta-llama/llama-3-70b"],
        "features": ["multi_provider", "fallback", "cost_optimization"]
    },
    "replicate": {
        "name": "Replicate",
        "type": "hosting",
        "adapter": "llm_service_adapter",
        "description": "Run open-source models in the cloud",
        "models": ["llama-3-70b", "mistral-7b", "flux-schnell"],
        "features": ["open_source", "custom_models", "image_generation"]
    },
    "groq": {
        "name": "Groq",
        "type": "inference",
        "adapter": "llm_service_adapter",
        "description": "Ultra-fast LLM inference",
        "models": ["llama3-8b", "llama3-70b", "mixtral-8x7b"],
        "features": ["fast", "cheap", "open_models"]
    },
    "together": {
        "name": "Together AI",
        "type": "inference",
        "adapter": "llm_service_adapter",
        "description": "Inference API for open-source models",
        "models": ["llama-3-70b", "mixtral-8x22b"],
        "features": ["open_source", "fine_tuning"]
    }
}


def list_llm_services() -> List[Dict]:
    """List all available LLM services"""
    return [
        {"id": key, **value}
        for key, value in LLM_SERVICES.items()
    ]


async def route_to_best_provider(messages: List[Dict], task_id: str,
                                 preferences: Optional[Dict] = None) -> Dict[str, Any]:
    """Intelligently route to best LLM provider based on:
    - Cost (cheapest)
    - Speed (fastest)
    - Quality (best model)
    - Availability
    """
    preferences = preferences or {}
    priority = preferences.get("priority", "balanced")  # cost, speed, quality
    
    # Simple routing logic (can be enhanced)
    if priority == "cost":
        provider = "groq"  # Cheapest
    elif priority == "speed":
        provider = "groq"  # Fastest
    elif priority == "quality":
        provider = "openrouter"  # Access to best models
    else:
        provider = "openrouter"  # Balanced
    
    adapter = UnifiedLLMAdapter(provider)
    try:
        result = await adapter.chat(messages, task_id, 
                                    model=preferences.get("model"))
        result["provider_used"] = provider
        return result
    finally:
        await adapter.close()
