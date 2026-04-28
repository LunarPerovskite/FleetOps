"""Agent Model Manager for FleetOps

Manages which models each agent uses, with:
- Per-agent model preferences
- Dynamic model switching
- Fallback chains
- Usage tracking per agent+model
- Cost optimization

Example:
    # User with Cline switches from Claude to GPT-4o
    manager = AgentModelManager()
    
    # Agent "juanes-cline-001" starts with Claude
    manager.set_model("juanes-cline-001", "claude-3-5-sonnet")
    
    # User switches to GPT-4o in Cline settings
    manager.set_model("juanes-cline-001", "gpt-4o")
    
    # Agent now routes through GPT-4o
    response = await manager.chat("juanes-cline-001", messages)
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from app.core.model_registry import (
    ModelRegistry, LLMModel, ModelCapability, ModelTier
)
from app.core.cost_tracking import cost_tracker
from app.core.usage_extraction import RealUsageExtractor
from app.core.logging_config import get_logger

logger = get_logger("fleetops.agent_model_manager")


class RoutingStrategy(str, Enum):
    """How to route requests"""
    FIXED = "fixed"           # Always use the assigned model
    CHEAPEST = "cheapest"     # Auto-switch to cheapest model
    FASTEST = "fastest"       # Auto-switch to fastest model
    BALANCED = "balanced"     # Balance cost vs performance
    FALLBACK = "fallback"     # Use fallback chain
    SMART = "smart"          # AI-powered routing


@dataclass
class AgentModelConfig:
    """Configuration for an agent's model usage"""
    agent_id: str
    user_id: str
    
    # Model assignment
    primary_model: str                    # Default model to use
    fallback_models: List[str] = field(default_factory=list)
    
    # Routing
    strategy: RoutingStrategy = RoutingStrategy.FIXED
    
    # Constraints
    max_cost_per_request: Optional[float] = None
    max_cost_per_day: Optional[float] = None
    required_capabilities: List[ModelCapability] = field(default_factory=list)
    allowed_providers: List[str] = field(default_factory=list)
    blocked_models: List[str] = field(default_factory=list)
    
    # Optimization
    auto_fallback: bool = True
    cost_optimization: bool = False
    latency_optimization: bool = False
    
    # Usage tracking
    today_cost: float = 0.0
    today_requests: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    
    def can_use_model(self, model: LLMModel) -> bool:
        """Check if this config allows using a specific model"""
        # Check blocked
        if model.id in self.blocked_models:
            return False
        
        # Check providers
        if self.allowed_providers and model.provider not in self.allowed_providers:
            return False
        
        # Check capabilities
        if self.required_capabilities and not model.can_handle(self.required_capabilities):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "primary_model": self.primary_model,
            "fallback_models": self.fallback_models,
            "strategy": self.strategy.value,
            "constraints": {
                "max_cost_per_request": self.max_cost_per_request,
                "max_cost_per_day": self.max_cost_per_day,
                "required_capabilities": [c.value for c in self.required_capabilities],
                "allowed_providers": self.allowed_providers,
                "blocked_models": self.blocked_models
            },
            "optimization": {
                "auto_fallback": self.auto_fallback,
                "cost_optimization": self.cost_optimization,
                "latency_optimization": self.latency_optimization
            },
            "usage_today": {
                "cost_usd": round(self.today_cost, 4),
                "requests": self.today_requests
            }
        }


class AgentModelManager:
    """Manages model assignments and routing for agents"""
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
        self._configs: Dict[str, AgentModelConfig] = {}  # agent_id -> config
        self._provider_adapters: Dict[str, Any] = {}       # provider -> adapter
        self._usage_cache: Dict[str, Dict] = {}          # agent_id -> usage
        
        # Initialize provider adapters
        self._init_adapters()
    
    def _init_adapters(self):
        """Lazy-load provider adapters"""
        try:
            from app.adapters.llm_providers import (
                OpenAIAdapter, AnthropicAdapter, GeminiAdapter, AzureOpenAIAdapter
            )
            self._provider_adapters = {
                "openai": OpenAIAdapter(),
                "anthropic": AnthropicAdapter(),
                "gemini": GeminiAdapter(),
                "azure": AzureOpenAIAdapter(),
            }
            logger.info(f"Initialized {len(self._provider_adapters)} provider adapters")
        except Exception as e:
            logger.error(f"Failed to initialize adapters: {e}")
    
    def configure_agent(self,
                       agent_id: str,
                       user_id: str,
                       primary_model: str,
                       **kwargs) -> AgentModelConfig:
        """Configure an agent's model settings"""
        
        # Build fallback chain if not provided
        fallback_models = kwargs.pop('fallback_models', None)
        if fallback_models is None:
            # Auto-generate fallback chain based on capabilities
            primary = self.registry.get(primary_model)
            if primary:
                # Find similar models from other providers
                same_tier = self.registry.find_models(
                    capabilities=primary.capabilities,
                    tier=primary.tier,
                    available_only=True
                )
                fallback_models = [m.id for m in same_tier 
                                 if m.id != primary_model and m.provider != primary.provider][:2]
        
        # Build config from kwargs
        config_kwargs = {
            'agent_id': agent_id,
            'user_id': user_id,
            'primary_model': primary_model,
            'fallback_models': fallback_models or [],
        }
        
        # Only pass valid fields
        valid_fields = set(AgentModelConfig.__dataclass_fields__.keys())
        for k, v in kwargs.items():
            if k in valid_fields:
                config_kwargs[k] = v
        
        config = AgentModelConfig(**config_kwargs)
        
        self._configs[agent_id] = config
        logger.info(f"Configured agent {agent_id}: {primary_model}")
        return config
    
    def get_config(self, agent_id: str) -> Optional[AgentModelConfig]:
        """Get agent's model configuration"""
        return self._configs.get(agent_id)
    
    def set_model(self, agent_id: str, model_id: str) -> bool:
        """Change an agent's active model"""
        config = self._configs.get(agent_id)
        if not config:
            logger.error(f"No config found for agent {agent_id}")
            return False
        
        model = self.registry.get(model_id)
        if not model:
            logger.error(f"Unknown model: {model_id}")
            return False
        
        if not config.can_use_model(model):
            logger.warning(f"Model {model_id} not allowed for agent {agent_id}")
            return False
        
        old_model = config.primary_model
        config.primary_model = model_id
        
        logger.info(f"Agent {agent_id} switched: {old_model} -> {model_id}")
        return True
    
    def _select_model(self, agent_id: str, 
                     estimated_input_tokens: int = 0,
                     required_capabilities: Optional[List[ModelCapability]] = None
                     ) -> Optional[LLMModel]:
        """Select the best model for a request based on strategy"""
        config = self._configs.get(agent_id)
        if not config:
            return None
        
        # Get primary model
        primary = self.registry.get(config.primary_model)
        if not primary:
            return None
        
        # Check if primary is available
        if primary.is_available and config.can_use_model(primary):
            if required_capabilities and not primary.can_handle(required_capabilities):
                # Primary can't handle it, need fallback
                pass
            else:
                return primary
        
        # Primary unavailable or unsuitable - use fallback chain
        for fallback_id in config.fallback_models:
            fallback = self.registry.get(fallback_id)
            if fallback and fallback.is_available and config.can_use_model(fallback):
                if not required_capabilities or fallback.can_handle(required_capabilities):
                    logger.info(f"Using fallback model {fallback_id} for {agent_id}")
                    return fallback
        
        # Strategy-based selection
        if config.strategy == RoutingStrategy.CHEAPEST:
            caps = required_capabilities or config.required_capabilities
            cheapest = self.registry.get_cheapest(
                capabilities=caps or None,
                provider=config.allowed_providers[0] if config.allowed_providers else None
            )
            if cheapest and config.can_use_model(cheapest):
                return cheapest
        
        elif config.strategy == RoutingStrategy.FASTEST:
            caps = required_capabilities or config.required_capabilities
            fastest = self.registry.get_fastest(caps or None)
            if fastest and config.can_use_model(fastest):
                return fastest
        
        # Last resort: try any available model with right capabilities
        if required_capabilities:
            candidates = self.registry.get_by_capability(required_capabilities[0])
            for model in candidates:
                if model.is_available and config.can_use_model(model):
                    if model.can_handle(required_capabilities):
                        return model
        
        return None
    
    async def chat(self,
                  agent_id: str,
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  temperature: float = 0.7,
                  max_tokens: int = 2048,
                  **kwargs) -> Dict[str, Any]:
        """Send a chat request through the appropriate model"""
        
        config = self._configs.get(agent_id)
        if not config:
            return {"status": "error", "error": f"Agent {agent_id} not configured"}
        
        # Determine model to use
        model_id = model or config.primary_model
        selected_model = self._select_model(agent_id)
        if not selected_model:
            return {"status": "error", "error": "No available model found"}
        
        # Check cost limits
        if config.max_cost_per_day and config.today_cost >= config.max_cost_per_day:
            return {
                "status": "error", 
                "error": f"Daily cost limit (${config.max_cost_per_day}) exceeded"
            }
        
        # Get provider adapter
        adapter = self._provider_adapters.get(selected_model.provider)
        if not adapter:
            return {"status": "error", "error": f"No adapter for {selected_model.provider}"}
        
        # Estimate cost before request
        input_estimate = sum(len(m.get("content", "")) // 4 for m in messages)
        estimated_cost = selected_model.estimate_cost(
            input_estimate, max_tokens
        )
        
        if config.max_cost_per_request and estimated_cost > config.max_cost_per_request:
            return {
                "status": "error",
                "error": f"Estimated cost (${estimated_cost:.4f}) exceeds per-request limit"
            }
        
        try:
            # Send request through adapter
            task_id = kwargs.get('task_id', f"{agent_id}-{datetime.utcnow().timestamp()}")
            
            result = await adapter.chat(
                messages=messages,
                task_id=task_id,
                model=selected_model.provider_model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                user_id=config.user_id
            )
            
            # Track usage
            if result.get("status") == "success":
                usage = result.get("usage", {})
                cost = result.get("cost_usd", 0)
                
                config.today_cost += cost
                config.today_requests += 1
                config.total_cost += cost
                config.total_requests += 1
                
                # Update model stats
                self.registry.update_latency(
                    selected_model.id,
                    kwargs.get('latency_ms', 1000)  # Would measure actual
                )
                
                logger.info(
                    f"Agent {agent_id} used {selected_model.id}: "
                    f"${cost:.4f}, {usage.get('total_tokens', 0)} tokens"
                )
            
            # Add routing metadata
            result["routing"] = {
                "model_used": selected_model.id,
                "provider": selected_model.provider,
                "strategy": config.strategy.value,
                "estimated_cost": estimated_cost,
                "agent_id": agent_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Chat failed for {agent_id}: {e}")
            
            # Mark model as potentially unavailable
            self.registry.update_availability(
                selected_model.id, 
                False,
                str(e)
            )
            
            # Try fallback if enabled
            if config.auto_fallback and config.fallback_models:
                logger.info(f"Attempting fallback for {agent_id}")
                # Remove failed model from consideration
                config.blocked_models.append(selected_model.id)
                
                fallback = self._select_model(agent_id)
                if fallback:
                    return await self.chat(agent_id, messages, 
                                         model=fallback.id, **kwargs)
            
            return {"status": "error", "error": str(e)}
    
    def get_agent_models(self, agent_id: str) -> Dict[str, Any]:
        """Get all available models for an agent"""
        config = self._configs.get(agent_id)
        if not config:
            return {"error": "Agent not configured"}
        
        # Get all models agent can use
        all_models = self.registry.find_models(available_only=True)
        allowed = [m for m in all_models if config.can_use_model(m)]
        blocked = [m for m in all_models if not config.can_use_model(m)]
        
        return {
            "agent_id": agent_id,
            "primary": config.primary_model,
            "fallbacks": config.fallback_models,
            "strategy": config.strategy.value,
            "allowed_models": [m.to_dict() for m in allowed],
            "blocked_models": [m.id for m in blocked],
            "current_usage": {
                "today_cost": round(config.today_cost, 4),
                "today_requests": config.today_requests
            }
        }
    
    def switch_provider(self, agent_id: str, 
                       provider: str,
                       model_id: Optional[str] = None) -> bool:
        """Switch an agent to a different provider entirely"""
        config = self._configs.get(agent_id)
        if not config:
            return False
        
        # Find best model on new provider
        if model_id:
            new_model = self.registry.get(model_id)
        else:
            # Get first available model from provider with right capabilities
            candidates = self.registry.get_by_provider(provider)
            new_model = None
            for m in candidates:
                if m.is_available:
                    new_model = m
                    break
        
        if not new_model:
            logger.error(f"No suitable model found on {provider}")
            return False
        
        old_provider = self.registry.get(config.primary_model)
        old_provider_name = old_provider.provider if old_provider else "unknown"
        
        config.primary_model = new_model.id
        config.allowed_providers = [provider]
        
        logger.info(
            f"Agent {agent_id} switched provider: "
            f"{old_provider_name} -> {provider} ({new_model.id})"
        )
        return True
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all configured agents"""
        return [config.to_dict() for config in self._configs.values()]
    
    def reset_daily_usage(self):
        """Reset daily counters (call at midnight)"""
        for config in self._configs.values():
            config.today_cost = 0.0
            config.today_requests = 0
        logger.info("Daily usage reset for all agents")


# Singleton
agent_model_manager = AgentModelManager()