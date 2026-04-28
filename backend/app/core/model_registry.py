"""LLM Model Registry for FleetOps

Central registry for all LLM models across all providers.

IMPORTANT: This registry starts EMPTY. All models come from
live discovery APIs (OpenRouter, provider APIs). No hardcoded
models that go stale.

To get models:
1. Run discovery: await discover_models()
2. Or register manually: model_registry.register(model)
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from app.core.logging_config import get_logger

logger = get_logger("fleetops.model_registry")


class ModelCapability(str, Enum):
    """What a model can do"""
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"
    FINE_TUNING = "fine_tuning"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    LONG_CONTEXT = "long_context"


class ModelTier(str, Enum):
    """Model quality/cost tier"""
    FREE = "free"
    CHEAP = "cheap"
    STANDARD = "standard"
    PREMIUM = "premium"
    ULTRA = "ultra"


@dataclass
class LLMModel:
    """Represents a single LLM model - always from live discovery"""
    id: str                          # "openai/gpt-4o", "anthropic/claude-3-7-sonnet"
    name: str                        # "GPT-4o", "Claude 3.7 Sonnet"
    provider: str                    # "openai", "anthropic", "gemini"
    provider_model_id: str           # Provider's internal ID
    
    # Capabilities
    capabilities: List[ModelCapability] = field(default_factory=list)
    
    # Cost per 1M tokens (USD)
    input_cost_per_1m: float = 0.0
    output_cost_per_1m: float = 0.0
    cached_input_cost_per_1m: Optional[float] = None
    
    # Context window
    max_input_tokens: int = 8192
    max_output_tokens: int = 4096
    max_total_tokens: int = 128000
    
    # Metadata
    tier: ModelTier = ModelTier.STANDARD
    description: str = ""
    release_date: Optional[str] = None
    supports_streaming: bool = True
    
    # Runtime state
    is_available: bool = True
    average_latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    last_used: Optional[datetime] = None
    request_count: int = 0
    
    # Discovery metadata
    discovered_from: str = ""         # "openrouter", "openai_api", "manual"
    discovered_at: Optional[datetime] = None
    raw_pricing: Optional[Dict] = None
    
    def estimate_cost(self, input_tokens: int, output_tokens: int,
                     cached_tokens: int = 0) -> float:
        """Estimate cost for a request in USD"""
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m
        
        # Cached tokens are cheaper
        if cached_tokens > 0 and self.cached_input_cost_per_1m:
            cached_cost = (cached_tokens / 1_000_000) * self.cached_input_cost_per_1m
            uncached_tokens = max(0, input_tokens - cached_tokens)
            uncached_cost = (uncached_tokens / 1_000_000) * self.input_cost_per_1m
            input_cost = cached_cost + uncached_cost
        
        return round(input_cost + output_cost, 6)
    
    def can_handle(self, required_capabilities: List[ModelCapability]) -> bool:
        """Check if model has all required capabilities"""
        return all(cap in self.capabilities for cap in required_capabilities)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "provider_model_id": self.provider_model_id,
            "capabilities": [c.value for c in self.capabilities],
            "cost_per_1m_tokens": {
                "input": self.input_cost_per_1m,
                "output": self.output_cost_per_1m,
                "cached_input": self.cached_input_cost_per_1m
            },
            "context_window": {
                "max_input": self.max_input_tokens,
                "max_output": self.max_output_tokens,
                "max_total": self.max_total_tokens
            },
            "tier": self.tier.value,
            "description": self.description,
            "is_available": self.is_available,
            "average_latency_ms": self.average_latency_ms,
            "supports_streaming": self.supports_streaming,
            "discovered_from": self.discovered_from,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }


class ModelRegistry:
    """Central registry for all LLM models - starts empty, populated by discovery"""
    
    def __init__(self):
        self._models: Dict[str, LLMModel] = {}
        self._provider_models: Dict[str, List[str]] = {}  # provider -> [model_ids]
        self._capability_models: Dict[ModelCapability, List[str]] = {}
        self._hooks: List[Callable] = []
        logger.info("ModelRegistry initialized (run discovery to populate)")
    
    def register(self, model: LLMModel):
        """Register a model from discovery"""
        self._models[model.id] = model
        
        # Update provider index
        if model.provider not in self._provider_models:
            self._provider_models[model.provider] = []
        if model.id not in self._provider_models[model.provider]:
            self._provider_models[model.provider].append(model.id)
        
        # Update capability index
        for cap in model.capabilities:
            if cap not in self._capability_models:
                self._capability_models[cap] = []
            if model.id not in self._capability_models[cap]:
                self._capability_models[cap].append(model.id)
        
        logger.info(f"Registered: {model.id} ({model.provider}) ${model.input_cost_per_1m}/1M")
        self._notify_hooks("registered", model)
    
    def update(self, model_id: str, **updates) -> bool:
        """Update a model's fields (e.g., pricing from discovery)"""
        model = self._models.get(model_id)
        if not model:
            return False
        
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        model.discovered_at = datetime.utcnow()
        logger.info(f"Updated: {model_id}")
        self._notify_hooks("updated", model)
        return True
    
    def get(self, model_id: str) -> Optional[LLMModel]:
        """Get model by ID"""
        return self._models.get(model_id)
    
    def get_by_provider(self, provider: str) -> List[LLMModel]:
        """Get all models for a provider"""
        model_ids = self._provider_models.get(provider, [])
        return [self._models[mid] for mid in model_ids if mid in self._models]
    
    def get_by_capability(self, capability: ModelCapability,
                         available_only: bool = True) -> List[LLMModel]:
        """Get models with specific capability"""
        model_ids = self._capability_models.get(capability, [])
        models = [self._models[mid] for mid in model_ids if mid in self._models]
        if available_only:
            models = [m for m in models if m.is_available]
        return models
    
    def find_models(self,
                   provider: Optional[str] = None,
                   capabilities: Optional[List[ModelCapability]] = None,
                   tier: Optional[ModelTier] = None,
                   max_cost_per_1m: Optional[float] = None,
                   available_only: bool = True) -> List[LLMModel]:
        """Find models matching criteria"""
        models = list(self._models.values())
        
        if available_only:
            models = [m for m in models if m.is_available]
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        if capabilities:
            models = [m for m in models if m.can_handle(capabilities)]
        
        if tier:
            models = [m for m in models if m.tier == tier]
        
        if max_cost_per_1m:
            models = [m for m in models 
                     if m.input_cost_per_1m <= max_cost_per_1m]
        
        return models
    
    def get_cheapest(self, 
                    capabilities: Optional[List[ModelCapability]] = None,
                    provider: Optional[str] = None) -> Optional[LLMModel]:
        """Get cheapest model matching criteria"""
        models = self.find_models(
            provider=provider,
            capabilities=capabilities
        )
        if not models:
            return None
        return min(models, key=lambda m: m.input_cost_per_1m + m.output_cost_per_1m)
    
    def get_fastest(self,
                   capabilities: Optional[List[ModelCapability]] = None) -> Optional[LLMModel]:
        """Get fastest model matching criteria"""
        models = self.find_models(capabilities=capabilities)
        if not models:
            return None
        return sorted(models, 
                     key=lambda m: m.average_latency_ms or float('inf'))[0]
    
    def update_availability(self, model_id: str, available: bool, 
                           error: Optional[str] = None):
        """Update model availability"""
        model = self._models.get(model_id)
        if model:
            model.is_available = available
            if error:
                model.last_error = error
            logger.info(f"Model {model_id} availability: {available}")
            self._notify_hooks("availability_changed", model)
    
    def update_latency(self, model_id: str, latency_ms: float):
        """Update model's average latency"""
        model = self._models.get(model_id)
        if model:
            if model.average_latency_ms is None:
                model.average_latency_ms = latency_ms
            else:
                # Exponential moving average
                model.average_latency_ms = 0.7 * model.average_latency_ms + 0.3 * latency_ms
            model.last_used = datetime.utcnow()
            model.request_count += 1
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered models"""
        return [m.to_dict() for m in self._models.values()]
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics by provider"""
        stats = {}
        for provider, model_ids in self._provider_models.items():
            models = [self._models[mid] for mid in model_ids if mid in self._models]
            stats[provider] = {
                "model_count": len(models),
                "available": len([m for m in models if m.is_available]),
                "min_cost": min(m.input_cost_per_1m for m in models) if models else 0,
                "max_cost": max(m.input_cost_per_1m for m in models) if models else 0,
            }
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall registry statistics"""
        all_models = list(self._models.values())
        available = [m for m in all_models if m.is_available]
        
        return {
            "total_models": len(all_models),
            "available": len(available),
            "unavailable": len(all_models) - len(available),
            "providers": list(self._provider_models.keys()),
            "provider_stats": self.get_provider_stats(),
            "last_updated": max(
                (m.discovered_at for m in all_models if m.discovered_at),
                default=None
            )
        }
    
    def clear(self):
        """Clear all models (useful for refresh)"""
        self._models.clear()
        self._provider_models.clear()
        self._capability_models.clear()
        logger.info("Registry cleared")
    
    def on_change(self, hook: Callable):
        """Register a hook for model changes"""
        self._hooks.append(hook)
    
    def _notify_hooks(self, event: str, model: LLMModel):
        """Notify all registered hooks"""
        for hook in self._hooks:
            try:
                hook(event, model)
            except Exception as e:
                logger.error(f"Hook error: {e}")


# Singleton - starts EMPTY
model_registry = ModelRegistry()


# ═══════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════

def get_model(model_id: str) -> Optional[LLMModel]:
    """Get model by ID"""
    return model_registry.get(model_id)

def list_models(provider: Optional[str] = None,
                capability: Optional[str] = None) -> List[Dict[str, Any]]:
    """List models with optional filtering"""
    if capability:
        cap = ModelCapability(capability)
        models = model_registry.get_by_capability(cap)
    elif provider:
        models = model_registry.get_by_provider(provider)
    else:
        models = list(model_registry._models.values())
    
    return [m.to_dict() for m in models if m.is_available]

def estimate_cost(model_id: str, input_tokens: int, 
                 output_tokens: int, cached_tokens: int = 0) -> Optional[float]:
    """Estimate cost for a request"""
    model = model_registry.get(model_id)
    if model:
        return model.estimate_cost(input_tokens, output_tokens, cached_tokens)
    return None
