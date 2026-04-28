"""LLM Model Registry for FleetOps

Central registry for all LLM models across all providers.
Handles:
- Model discovery and metadata
- Provider-to-model mapping
- Cost and capability tracking
- Health status monitoring
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
    """Represents a single LLM model"""
    id: str                          # "gpt-4o", "claude-3-5-sonnet"
    name: str                        # "GPT-4o", "Claude 3.5 Sonnet"
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
            "is_available": self.is_available,
            "average_latency_ms": self.average_latency_ms,
            "supports_streaming": self.supports_streaming
        }


class ModelRegistry:
    """Central registry for all LLM models"""
    
    def __init__(self):
        self._models: Dict[str, LLMModel] = {}
        self._provider_models: Dict[str, List[str]] = {}  # provider -> [model_ids]
        self._capability_models: Dict[ModelCapability, List[str]] = {}  # cap -> [model_ids]
        self._hooks: List[Callable] = []  # Change hooks
        self._load_builtin_models()
    
    def _load_builtin_models(self):
        """Load all known models with pricing"""
        
        # OpenAI models
        self.register(LLMModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            provider_model_id="gpt-4o",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE, ModelCapability.STREAMING
            ],
            input_cost_per_1m=2.50,
            output_cost_per_1m=10.00,
            cached_input_cost_per_1m=1.25,
            max_input_tokens=128000,
            max_output_tokens=16384,
            max_total_tokens=128000,
            tier=ModelTier.PREMIUM,
            description="OpenAI's flagship multimodal model"
        ))
        
        self.register(LLMModel(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            provider_model_id="gpt-4o-mini",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE, ModelCapability.STREAMING
            ],
            input_cost_per_1m=0.15,
            output_cost_per_1m=0.60,
            cached_input_cost_per_1m=0.075,
            max_input_tokens=128000,
            max_output_tokens=16384,
            tier=ModelTier.CHEAP,
            description="Fast, affordable model for most tasks"
        ))
        
        self.register(LLMModel(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider="openai",
            provider_model_id="gpt-4-turbo-preview",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.FUNCTION_CALLING, ModelCapability.JSON_MODE,
                ModelCapability.STREAMING, ModelCapability.LONG_CONTEXT
            ],
            input_cost_per_1m=10.00,
            output_cost_per_1m=30.00,
            max_input_tokens=128000,
            max_output_tokens=4096,
            tier=ModelTier.ULTRA,
            description="Legacy high-performance model"
        ))
        
        self.register(LLMModel(
            id="o1-preview",
            name="o1 Preview",
            provider="openai",
            provider_model_id="o1-preview",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.REASONING,
                ModelCapability.CODE, ModelCapability.STREAMING
            ],
            input_cost_per_1m=15.00,
            output_cost_per_1m=60.00,
            max_input_tokens=128000,
            max_output_tokens=32768,
            tier=ModelTier.ULTRA,
            description="Reasoning-focused model for complex tasks"
        ))
        
        # Anthropic models
        self.register(LLMModel(
            id="claude-3-5-sonnet",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            provider_model_id="claude-3-5-sonnet-20241022",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.FUNCTION_CALLING,
                ModelCapability.STREAMING, ModelCapability.LONG_CONTEXT
            ],
            input_cost_per_1m=3.00,
            output_cost_per_1m=15.00,
            max_input_tokens=200000,
            max_output_tokens=8192,
            max_total_tokens=200000,
            tier=ModelTier.PREMIUM,
            description="Best balance of performance and cost"
        ))
        
        self.register(LLMModel(
            id="claude-3-opus",
            name="Claude 3 Opus",
            provider="anthropic",
            provider_model_id="claude-3-opus-20240229",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.FUNCTION_CALLING,
                ModelCapability.STREAMING, ModelCapability.LONG_CONTEXT
            ],
            input_cost_per_1m=15.00,
            output_cost_per_1m=75.00,
            max_input_tokens=200000,
            max_output_tokens=4096,
            tier=ModelTier.ULTRA,
            description="Most capable Anthropic model"
        ))
        
        self.register(LLMModel(
            id="claude-3-haiku",
            name="Claude 3 Haiku",
            provider="anthropic",
            provider_model_id="claude-3-haiku-20240307",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.STREAMING
            ],
            input_cost_per_1m=0.25,
            output_cost_per_1m=1.25,
            max_input_tokens=200000,
            max_output_tokens=4096,
            tier=ModelTier.CHEAP,
            description="Fastest Claude model for simple tasks"
        ))
        
        # Gemini models
        self.register(LLMModel(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            provider="gemini",
            provider_model_id="gemini-1.5-pro",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.FUNCTION_CALLING,
                ModelCapability.STREAMING, ModelCapability.LONG_CONTEXT
            ],
            input_cost_per_1m=3.50,
            output_cost_per_1m=10.50,
            max_input_tokens=2000000,
            max_output_tokens=8192,
            tier=ModelTier.PREMIUM,
            description="Google's most capable model with 2M context"
        ))
        
        self.register(LLMModel(
            id="gemini-1.5-flash",
            name="Gemini 1.5 Flash",
            provider="gemini",
            provider_model_id="gemini-1.5-flash",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.STREAMING
            ],
            input_cost_per_1m=0.35,
            output_cost_per_1m=1.05,
            max_input_tokens=1000000,
            max_output_tokens=8192,
            tier=ModelTier.CHEAP,
            description="Fast Gemini model for high-volume tasks"
        ))
        
        # Azure OpenAI (same models, different provider)
        self.register(LLMModel(
            id="azure-gpt-4o",
            name="Azure GPT-4o",
            provider="azure",
            provider_model_id="gpt-4o",
            capabilities=[
                ModelCapability.CHAT, ModelCapability.CODE,
                ModelCapability.VISION, ModelCapability.FUNCTION_CALLING,
                ModelCapability.JSON_MODE, ModelCapability.STREAMING
            ],
            input_cost_per_1m=5.00,
            output_cost_per_1m=15.00,
            max_input_tokens=128000,
            max_output_tokens=16384,
            tier=ModelTier.PREMIUM,
            description="GPT-4o via Azure OpenAI"
        ))
    
    def register(self, model: LLMModel):
        """Register a new model"""
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
        
        logger.info(f"Registered model: {model.id} ({model.provider})")
        self._notify_hooks("registered", model)
    
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
        # Sort by latency (None last)
        return sorted(models, 
                     key=lambda m: m.average_latency_ms or float('inf'))[0]
    
    def update_availability(self, model_id: str, available: bool, 
                           error: Optional[str] = None):
        """Update model availability (e.g., after circuit breaker trip)"""
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


# Singleton
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