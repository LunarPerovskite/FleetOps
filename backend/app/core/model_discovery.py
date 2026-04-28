"""Dynamic Model Discovery for FleetOps

Fetches REAL models from multiple provider APIs:
- Direct providers: OpenAI, Anthropic, Gemini, DeepSeek, Mistral, Cohere, Z.ai, MiniMax, ElevenLabs
- Aggregators: OpenRouter (100+ models from all providers)
- Local: Ollama

Each connector hits the actual provider API for live pricing.
Users see ACTUAL latest models with real costs.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from app.core.model_registry import LLMModel, ModelCapability, ModelTier, model_registry
from app.core.model_providers import (
    get_connector, list_supported_providers
)
from app.core.logging_config import get_logger

logger = get_logger("fleetops.model_discovery")


class ModelDiscoveryService:
    """Discovers models from ALL sources: direct providers + OpenRouter + local"""
    
    def __init__(self):
        self._last_discovery: Optional[datetime] = None
        self._discovered_models: Dict[str, Dict] = {}
        self._connectors: Dict[str, Any] = {}
    
    async def discover_from_provider(self, provider: str, **kwargs) -> List[Dict[str, Any]]:
        """Discover models from a single provider"""
        
        connector = get_connector(provider, **kwargs)
        if not connector:
            logger.warning(f"Unknown provider: {provider}")
            return []
        
        try:
            models = await connector.list_models()
            logger.info(f"Discovered {len(models)} models from {provider}")
            
            # Store
            for m in models:
                m["discovered_from"] = provider
                m["discovered_at"] = datetime.utcnow().isoformat()
                self._discovered_models[m["id"]] = m
            
            return models
            
        except Exception as e:
            logger.error(f"Discovery failed for {provider}: {e}")
            return []
        finally:
            await connector.close()
    
    async def discover_all(self, providers: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Discover models from all configured providers
        
        Args:
            providers: List of provider IDs to discover from.
                      If None, discovers from all providers with API keys.
        
        Returns:
            Dict mapping provider -> list of models
        """
        
        if providers is None:
            # Discover from all supported providers
            providers = [p["id"] for p in list_supported_providers()]
        
        results = {}
        
        for provider in providers:
            models = await self.discover_from_provider(provider)
            results[provider] = models
        
        self._last_discovery = datetime.utcnow()
        
        total = sum(len(v) for v in results.values())
        logger.info(f"Total discovered from {len(providers)} providers: {total}")
        
        return results
    
    def register_model(self, model_data: Dict) -> bool:
        """Register a discovered model in the global registry"""
        
        try:
            pricing = model_data.get("pricing", {})
            
            model = LLMModel(
                id=model_data["id"],
                name=model_data["name"],
                provider=model_data["provider"],
                provider_model_id=model_data["provider_model_id"],
                capabilities=[
                    ModelCapability(c) for c in model_data.get("capabilities", ["chat"])
                    if c in [m.value for m in ModelCapability]
                ],
                input_cost_per_1m=pricing.get("input", 0),
                output_cost_per_1m=pricing.get("output", 0),
                max_input_tokens=model_data.get("context_length") or 128000,
                max_output_tokens=4096,
                max_total_tokens=model_data.get("context_length") or 128000,
                tier=self._infer_tier(pricing),
                description=f"{model_data.get('type', 'chat')} model from {model_data['provider']}",
                discovered_from=model_data.get("discovered_from", "unknown"),
                discovered_at=datetime.utcnow()
            )
            
            model_registry.register(model)
            return True
            
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return False
    
    def register_all(self, provider: Optional[str] = None) -> int:
        """Register all discovered models"""
        
        registered = 0
        for model_id, model_data in self._discovered_models.items():
            if provider and model_data.get("discovered_from") != provider:
                continue
            
            if self.register_model(model_data):
                registered += 1
        
        return registered
    
    def _infer_tier(self, pricing: Dict) -> ModelTier:
        """Infer tier from pricing"""
        input_cost = pricing.get("input", 0)
        
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
    
    def search(self, query: str = "",
               provider: Optional[str] = None,
               model_type: Optional[str] = None,
               capability: Optional[str] = None,
               max_cost: Optional[float] = None) -> List[Dict]:
        """Search discovered models"""
        
        results = []
        for m in self._discovered_models.values():
            # Filter by query
            if query and query.lower() not in m.get("name", "").lower() and \
               query.lower() not in m.get("id", "").lower():
                continue
            
            # Filter by provider
            if provider and m.get("provider") != provider:
                continue
            
            # Filter by type
            if model_type and m.get("type") != model_type:
                continue
            
            # Filter by capability
            if capability and capability not in m.get("capabilities", []):
                continue
            
            # Filter by cost
            if max_cost:
                price = m.get("pricing", {}).get("input", 0)
                if price > max_cost:
                    continue
            
            results.append(m)
        
        return sorted(results, key=lambda m: m.get("pricing", {}).get("input", 0))
    
    def get_by_type(self, model_type: str) -> List[Dict]:
        """Get models by type (chat, embedding, audio, image, etc.)"""
        return [m for m in self._discovered_models.values() if m.get("type") == model_type]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        
        by_provider = {}
        by_type = {}
        
        for m in self._discovered_models.values():
            provider = m.get("provider", "unknown")
            model_type = m.get("type", "unknown")
            
            by_provider[provider] = by_provider.get(provider, 0) + 1
            by_type[model_type] = by_type.get(model_type, 0) + 1
        
        return {
            "total_discovered": len(self._discovered_models),
            "by_provider": by_provider,
            "by_type": by_type,
            "last_discovery": self._last_discovery.isoformat() if self._last_discovery else None,
            "registered": len(model_registry._models)
        }


# Singleton
discovery_service = ModelDiscoveryService()


# ═══════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════

async def discover_from_provider(provider: str, **kwargs) -> List[Dict]:
    """Discover from a specific provider"""
    return await discovery_service.discover_from_provider(provider, **kwargs)

async def discover_all_models(providers: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
    """Discover from all providers"""
    return await discovery_service.discover_all(providers)

def get_chat_models() -> List[Dict]:
    """Get all chat models"""
    return discovery_service.get_by_type("chat")

def get_embedding_models() -> List[Dict]:
    """Get all embedding models"""
    return discovery_service.get_by_type("embedding")

def get_audio_models() -> List[Dict]:
    """Get all audio models (TTS, transcription)"""
    return discovery_service.get_by_type("audio_generation") + \
           discovery_service.get_by_type("audio_transcription")

def get_image_models() -> List[Dict]:
    """Get all image generation models"""
    return discovery_service.get_by_type("image_generation")

def search_models(query: str = "", **filters) -> List[Dict]:
    """Search discovered models"""
    return discovery_service.search(query, **filters)