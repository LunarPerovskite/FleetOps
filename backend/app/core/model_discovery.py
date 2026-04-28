"""Dynamic Model Discovery for FleetOps

Discovers models from various providers dynamically:
- OpenRouter (aggregates 100+ models)
- Ollama (local models)
- OpenAI (list models API)
- Anthropic (static list)
- Custom providers

Users can:
- Browse all available models
- Add custom models
- Search by capability, cost, provider
"""

from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass
from datetime import datetime
import httpx
import json
import asyncio

from app.core.model_registry import (
    LLMModel, ModelCapability, ModelTier, model_registry
)
from app.core.logging_config import get_logger

logger = get_logger("fleetops.model_discovery")


@dataclass
class DiscoveredModel:
    """Model discovered from a provider API"""
    id: str
    name: str
    provider: str
    provider_model_id: str
    context_length: Optional[int] = None
    pricing: Optional[Dict[str, float]] = None
    capabilities: List[str] = None
    raw_data: Dict = None
    discovered_at: datetime = None
    
    def to_llm_model(self) -> LLMModel:
        """Convert discovery result to registry model"""
        p = self.pricing or {}
        return LLMModel(
            id=self.id,
            name=self.name,
            provider=self.provider,
            provider_model_id=self.provider_model_id,
            capabilities=self._infer_capabilities(),
            input_cost_per_1m=p.get("input", 0) * 1_000_000,
            output_cost_per_1m=p.get("output", 0) * 1_000_000,
            max_input_tokens=self.context_length or 128000,
            max_output_tokens=4096,
            max_total_tokens=self.context_length or 128000,
            tier=self._infer_tier(),
            description=f"Discovered from {self.provider}"
        )
    
    def _infer_capabilities(self) -> List[ModelCapability]:
        """Infer capabilities from model ID/name"""
        caps = [ModelCapability.CHAT, ModelCapability.STREAMING]
        name_lower = self.name.lower()
        id_lower = self.id.lower()
        
        if any(x in name_lower for x in ["vision", "gpt-4o", "claude-3", "gemini"]):
            caps.append(ModelCapability.VISION)
        if any(x in name_lower for x in ["code", "coder", "devin"]):
            caps.append(ModelCapability.CODE)
        if any(x in name_lower for x in ["function", "tool"]):
            caps.append(ModelCapability.FUNCTION_CALLING)
        if "json" in name_lower or "openai" in id_lower:
            caps.append(ModelCapability.JSON_MODE)
        if self.context_length and self.context_length > 100000:
            caps.append(ModelCapability.LONG_CONTEXT)
        
        if self.capabilities:
            for c in self.capabilities:
                try:
                    caps.append(ModelCapability(c))
                except:
                    pass
        
        return list(set(caps))
    
    def _infer_tier(self) -> ModelTier:
        """Infer tier from pricing"""
        if not self.pricing:
            return ModelTier.STANDARD
        
        input_cost = self.pricing.get("input", 0) * 1_000_000
        
        if input_cost == 0:
            return ModelTier.FREE
        elif input_cost < 1:
            return ModelTier.CHEAP
        elif input_cost < 5:
            return ModelTier.STANDARD
        elif input_cost < 20:
            return ModelTier.PREMIUM
        else:
            return ModelTier.ULTRA


class OpenRouterDiscovery:
    """Discover models from OpenRouter API"""
    
    API_URL = "https://openrouter.ai/api/v1/models"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.client = httpx.AsyncClient(timeout=30)
    
    async def discover(self) -> List[DiscoveredModel]:
        """Fetch all models from OpenRouter"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(self.API_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            models = []
            for item in data.get("data", []):
                # Extract pricing
                pricing = item.get("pricing", {})
                
                models.append(DiscoveredModel(
                    id=f"openrouter/{item['id']}",
                    name=item.get("name", item["id"]),
                    provider="openrouter",
                    provider_model_id=item["id"],
                    context_length=item.get("context_length"),
                    pricing={
                        "prompt": float(pricing.get("prompt", 0) or 0),
                        "completion": float(pricing.get("completion", 0) or 0)
                    } if pricing else None,
                    raw_data=item,
                    discovered_at=datetime.utcnow()
                ))
            
            logger.info(f"Discovered {len(models)} models from OpenRouter")
            return models
            
        except Exception as e:
            logger.error(f"OpenRouter discovery failed: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


class OllamaDiscovery:
    """Discover local models from Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10)
    
    async def discover(self) -> List[DiscoveredModel]:
        """Fetch local models from Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for item in data.get("models", []):
                model_id = item["name"]
                models.append(DiscoveredModel(
                    id=f"ollama/{model_id}",
                    name=model_id,
                    provider="ollama",
                    provider_model_id=model_id,
                    context_length=None,  # Ollama doesn't report this
                    pricing={"prompt": 0, "completion": 0},  # Free (local)
                    raw_data=item,
                    discovered_at=datetime.utcnow()
                ))
            
            logger.info(f"Discovered {len(models)} models from Ollama")
            return models
            
        except httpx.ConnectError:
            logger.info("Ollama not running, skipping local discovery")
            return []
        except Exception as e:
            logger.error(f"Ollama discovery failed: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


class OpenAIDiscovery:
    """Discover models from OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=30
        )
    
    async def discover(self) -> List[DiscoveredModel]:
        """Fetch models from OpenAI"""
        if not self.api_key:
            logger.info("No OpenAI API key, skipping discovery")
            return []
        
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for item in data.get("data", []):
                model_id = item["id"]
                # Skip non-chat models
                if not any(x in model_id for x in ["gpt", "o1", "davinci"]):
                    continue
                
                models.append(DiscoveredModel(
                    id=model_id,
                    name=item.get("name", model_id),
                    provider="openai",
                    provider_model_id=model_id,
                    raw_data=item,
                    discovered_at=datetime.utcnow()
                ))
            
            logger.info(f"Discovered {len(models)} models from OpenAI")
            return models
            
        except Exception as e:
            logger.error(f"OpenAI discovery failed: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


class ModelDiscoveryService:
    """Service that discovers and registers models from all sources"""
    
    def __init__(self):
        self.discoverers = {
            "openrouter": OpenRouterDiscovery(),
            "ollama": OllamaDiscovery(),
            "openai": OpenAIDiscovery(),
        }
        self._last_discovery: Optional[datetime] = None
        self._discovered_models: Dict[str, DiscoveredModel] = {}
    
    async def discover_all(self, sources: Optional[List[str]] = None) -> Dict[str, List[DiscoveredModel]]:
        """Discover models from all configured sources"""
        
        sources = sources or list(self.discoverers.keys())
        results = {}
        
        for source in sources:
            discoverer = self.discoverers.get(source)
            if discoverer:
                try:
                    models = await discoverer.discover()
                    results[source] = models
                    
                    # Store in cache
                    for m in models:
                        self._discovered_models[m.id] = m
                except Exception as e:
                    logger.error(f"Discovery failed for {source}: {e}")
                    results[source] = []
        
        self._last_discovery = datetime.utcnow()
        total = sum(len(v) for v in results.values())
        logger.info(f"Total discovered models: {total}")
        
        return results
    
    def register_discovered(self, model_id: str) -> bool:
        """Register a discovered model in the global registry"""
        
        discovered = self._discovered_models.get(model_id)
        if not discovered:
            logger.error(f"Model {model_id} not in discovery cache")
            return False
        
        try:
            llm_model = discovered.to_llm_model()
            model_registry.register(llm_model)
            logger.info(f"Registered discovered model: {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register {model_id}: {e}")
            return False
    
    def register_all_discovered(self, source: Optional[str] = None) -> int:
        """Register all discovered models"""
        
        registered = 0
        for model_id, discovered in self._discovered_models.items():
            if source and discovered.provider != source:
                continue
            
            if self.register_discovered(model_id):
                registered += 1
        
        return registered
    
    def search(self, query: str = "", 
               provider: Optional[str] = None,
               capability: Optional[str] = None,
               max_cost: Optional[float] = None) -> List[Dict[str, Any]]:
        """Search discovered models"""
        
        results = []
        for model in self._discovered_models.values():
            # Filter by query
            if query and query.lower() not in model.name.lower() and query.lower() not in model.id.lower():
                continue
            
            # Filter by provider
            if provider and model.provider != provider:
                continue
            
            # Filter by capability
            if capability and capability not in (model.capabilities or []):
                continue
            
            # Filter by cost
            if max_cost and model.pricing:
                if model.pricing.get("prompt", 0) * 1_000_000 > max_cost:
                    continue
            
            results.append({
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "context_length": model.context_length,
                "pricing": model.pricing,
                "capabilities": model.capabilities,
                "discovered_at": model.discovered_at.isoformat() if model.discovered_at else None
            })
        
        return sorted(results, key=lambda m: m.get("pricing", {}).get("prompt", 0))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        
        by_provider = {}
        for model in self._discovered_models.values():
            provider = model.provider
            if provider not in by_provider:
                by_provider[provider] = 0
            by_provider[provider] += 1
        
        return {
            "total_discovered": len(self._discovered_models),
            "by_provider": by_provider,
            "last_discovery": self._last_discovery.isoformat() if self._last_discovery else None,
            "registered_in_registry": len([
                m for m in self._discovered_models 
                if m.id in model_registry._models
            ])
        }
    
    async def close(self):
        """Close all discoverer connections"""
        for discoverer in self.discoverers.values():
            try:
                await discoverer.close()
            except:
                pass


# Singleton
discovery_service = ModelDiscoveryService()


# ═══════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════

async def discover_models(sources: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
    """Discover models from all sources"""
    results = await discovery_service.discover_all(sources)
    return {
        source: [{
            "id": m.id,
            "name": m.name,
            "provider": m.provider,
            "context_length": m.context_length,
            "pricing": m.pricing
        } for m in models]
        for source, models in results.items()
    }

def register_discovered_model(model_id: str) -> bool:
    """Register a single discovered model"""
    return discovery_service.register_discovered(model_id)

def search_models(query: str = "", **filters) -> List[Dict]:
    """Search discovered models"""
    return discovery_service.search(query, **filters)

def get_discovery_stats() -> Dict[str, Any]:
    """Get discovery statistics"""
    return discovery_service.get_stats()