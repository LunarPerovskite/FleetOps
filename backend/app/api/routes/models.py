"""Model Selection API for FleetOps

REST API endpoints for model management:
- List available models
- Search/filter models
- Select model for agent
- Configure model preferences
- Switch between models
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.core.model_registry import model_registry, LLMModel, ModelCapability, ModelTier
from app.core.agent_model_manager import agent_model_manager, RoutingStrategy
from app.core.model_discovery import discovery_service
from app.core.auto_discovery_service import auto_discovery
from app.core.logging_config import get_logger
from app.api.routes.auth import get_current_user
from app.models.models import User

logger = get_logger("fleetops.api.models")

router = APIRouter(prefix="/models", tags=["models"])


# ═══════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    capabilities: List[str]
    cost_per_1m_tokens: Dict[str, Optional[float]]
    context_window: Dict[str, int]
    tier: str
    is_available: bool
    average_latency_ms: Optional[float] = None

class ModelSearchRequest(BaseModel):
    query: str = ""
    provider: Optional[str] = None
    capability: Optional[str] = None
    max_cost_per_1m: Optional[float] = None
    tier: Optional[str] = None
    available_only: bool = True

class ModelSelectRequest(BaseModel):
    agent_id: str
    model_id: str
    user_id: str

class AgentModelConfig(BaseModel):
    agent_id: str
    user_id: str
    primary_model: str
    fallback_models: List[str]
    strategy: str
    constraints: Dict[str, Any]
    optimization: Dict[str, Any]
    usage_today: Dict[str, Any]

class ModelSwitchRequest(BaseModel):
    agent_id: str
    new_model_id: str
    reason: Optional[str] = None


# ═══════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════

@router.get("/", response_model=List[ModelInfo])
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    capability: Optional[str] = Query(None, description="Filter by capability (chat, code, vision, etc.)"),
    max_cost: Optional[float] = Query(None, description="Max cost per 1M input tokens (USD)"),
    tier: Optional[str] = Query(None, description="Filter by tier (free, cheap, standard, premium, ultra)"),
    available_only: bool = Query(True, description="Only show available models"),
    search: Optional[str] = Query(None, description="Search by name or ID")
):
    """List all available models with optional filtering
    
    Examples:
        GET /api/v1/models/ - All models
        GET /api/v1/models/?provider=openai - Only OpenAI
        GET /api/v1/models/?capability=code - Code-capable models
        GET /api/v1/models/?max_cost=5 - Under $5/1M tokens
        GET /api/v1/models/?search=claude - Search for Claude
    """
    
    # Convert capability string to enum
    capabilities = None
    if capability:
        try:
            capabilities = [ModelCapability(capability)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown capability: {capability}")
    
    # Convert tier
    tier_enum = None
    if tier:
        try:
            tier_enum = ModelTier(tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown tier: {tier}")
    
    # Search in both registry and discovered models
    models = model_registry.find_models(
        provider=provider,
        capabilities=capabilities,
        tier=tier_enum,
        max_cost_per_1m=max_cost,
        available_only=available_only
    )
    
    # Filter by search query
    if search:
        search_lower = search.lower()
        models = [m for m in models 
                 if search_lower in m.id.lower() or search_lower in m.name.lower()]
    
    return [ModelInfo(**m.to_dict()) for m in models]


@router.get("/providers", response_model=List[Dict[str, Any]])
async def list_providers():
    """List all available providers with model counts"""
    
    providers = {}
    for model in model_registry._models.values():
        provider = model.provider
        if provider not in providers:
            providers[provider] = {
                "name": provider,
                "models": [],
                "model_count": 0,
                "tiers": set(),
                "min_cost": float('inf'),
                "max_cost": 0
            }
        
        providers[provider]["models"].append(model.id)
        providers[provider]["model_count"] += 1
        providers[provider]["tiers"].add(model.tier.value)
        providers[provider]["min_cost"] = min(providers[provider]["min_cost"], model.input_cost_per_1m)
        providers[provider]["max_cost"] = max(providers[provider]["max_cost"], model.input_cost_per_1m)
    
    # Convert to list and sort by model count
    result = []
    for name, data in providers.items():
        data["tiers"] = sorted(list(data["tiers"]))
        data.pop("models")  # Remove full list, keep count
        result.append(data)
    
    return sorted(result, key=lambda x: x["model_count"], reverse=True)


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """Get detailed info about a specific model"""
    
    model = model_registry.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    return ModelInfo(**model.to_dict())


@router.post("/{model_id}/select")
async def select_model(
    model_id: str,
    request: ModelSelectRequest
):
    """Select a model for an agent
    
    This is the main endpoint for model switching.
    Users select a model in the UI and this configures the agent.
    """
    
    model = model_registry.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    # Configure agent if not exists
    config = agent_model_manager.get_config(request.agent_id)
    if not config:
        config = agent_model_manager.configure_agent(
            agent_id=request.agent_id,
            user_id=request.user_id,
            primary_model=model_id
        )
    
    # Switch to new model
    success = agent_model_manager.set_model(request.agent_id, model_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to select model {model_id}")
    
    config = agent_model_manager.get_config(request.agent_id)
    
    return {
        "status": "success",
        "agent_id": request.agent_id,
        "model_id": model_id,
        "model_name": model.name,
        "provider": model.provider,
        "estimated_cost_per_1k_tokens": model.estimate_cost(1000, 500),
        "message": f"Model switched to {model.name}",
        "config": AgentModelConfig(**config.to_dict()).dict()
    }


@router.post("/{model_id}/estimate")
async def estimate_cost(
    model_id: str,
    input_tokens: int = Query(1000, description="Estimated input tokens"),
    output_tokens: int = Query(500, description="Estimated output tokens"),
    cached_tokens: int = Query(0, description="Cached input tokens")
):
    """Estimate cost for a request"""
    
    model = model_registry.get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    cost = model.estimate_cost(input_tokens, output_tokens, cached_tokens)
    
    return {
        "model_id": model_id,
        "model_name": model.name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "estimated_cost_usd": cost,
        "pricing": {
            "input_per_1m": model.input_cost_per_1m,
            "output_per_1m": model.output_cost_per_1m,
            "cached_input_per_1m": model.cached_input_cost_per_1m
        }
    }


@router.get("/agent/{agent_id}")
async def get_agent_models(agent_id: str):
    """Get all models available to an agent with current config"""
    
    result = agent_model_manager.get_agent_models(agent_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/agent/{agent_id}/switch")
async def switch_agent_model(
    agent_id: str,
    request: ModelSwitchRequest
):
    """Switch an agent's model"""
    
    if agent_id != request.agent_id:
        raise HTTPException(status_code=400, detail="Agent ID mismatch")
    
    config = agent_model_manager.get_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    old_model = config.primary_model
    
    success = agent_model_manager.set_model(agent_id, request.new_model_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to switch model")
    
    new_model = model_registry.get(request.new_model_id)
    
    return {
        "status": "success",
        "agent_id": agent_id,
        "old_model": old_model,
        "new_model": request.new_model_id,
        "new_model_name": new_model.name if new_model else request.new_model_id,
        "reason": request.reason,
        "message": f"Switched from {old_model} to {request.new_model_id}"
    }


@router.get("/agent/{agent_id}/usage")
async def get_agent_usage(agent_id: str):
    """Get usage statistics for an agent"""
    
    config = agent_model_manager.get_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "agent_id": agent_id,
        "today": {
            "cost_usd": round(config.today_cost, 4),
            "requests": config.today_requests
        },
        "total": {
            "cost_usd": round(config.total_cost, 4),
            "requests": config.total_requests
        },
        "primary_model": config.primary_model,
        "fallback_models": config.fallback_models,
        "strategy": config.strategy.value
    }


# ═══════════════════════════════════════
# Discovery Endpoints
# ═══════════════════════════════════════

@router.post("/discover")
async def discover_models(
    sources: Optional[List[str]] = Query(None, description="Sources to discover from")
):
    """Discover models from external providers
    
    Sources:
        - openrouter: 100+ models via OpenRouter
        - ollama: Local models
        - openai: OpenAI API
    """
    
    results = await discovery_service.discover_all(sources)
    
    return {
        "status": "success",
        "sources": {
            source: len(models) for source, models in results.items()
        },
        "total_discovered": sum(len(v) for v in results.values()),
        "message": "Discovery complete. Use POST /models/register to add to registry."
    }


@router.post("/discover/auto")
async def auto_discover_models(
    provider: Optional[str] = Query(None, description="Specific provider to discover, or all if omitted")
):
    """Auto-discover models using configured API keys.
    
    This endpoint uses the AutoDiscoveryService which reads API keys from:
    1. Environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
    2. Future: organization secrets store
    
    No manual model list needed — just configure your keys and FleetOps
    finds everything available.
    """
    
    if provider:
        results = await auto_discovery.discover_provider(provider)
        return {
            "status": "success",
            "provider": provider,
            "models_discovered": len(results),
            "models": results,
        }
    else:
        results = await auto_discovery.discover_all_configured()
        return {
            "status": "success",
            "providers": {
                p: len(m) for p, m in results.items()
            },
            "total_discovered": sum(len(v) for v in results.values()),
            "message": "Auto-discovery complete. Models registered automatically.",
        }


@router.post("/providers/{provider}/refresh-key")
async def refresh_provider_key(
    provider: str,
    api_key: str,
    current_user: User = Depends(get_current_user)
):
    """Update API key for a provider and auto-discover models.
    
    This is the main endpoint for the Settings → Providers UI.
    When user pastes a new API key, FleetOps:
    1. Validates the key (test call)
    2. Discovers all available models
    3. Registers them in the global registry
    4. Returns the discovered models
    """
    
    from app.core.auth import verify_token
    
    # TODO: Save key to secrets store for the org
    # For now, discovery uses the provided key directly
    
    result = await auto_discovery.refresh_on_key_update(provider, api_key)
    
    return {
        "status": "success",
        "provider": provider,
        **result,
        "message": f"Discovered {result['models_discovered']} models from {provider}",
    }


@router.get("/providers/status")
async def get_provider_discovery_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all providers: which have API keys, how many models registered.
    
    Frontend uses this to show:
    - Provider cards with "Connected" / "Not configured" badges
    - Model count per provider
    - "Add key" buttons for unconfigured providers
    """
    
    return auto_discovery.get_provider_status()


@router.post("/register")
async def register_discovered(
    model_ids: List[str],
    source: Optional[str] = None
):
    """Register discovered models in the global registry"""
    
    registered = 0
    failed = []
    
    for model_id in model_ids:
        if discovery_service.register_discovered(model_id):
            registered += 1
        else:
            failed.append(model_id)
    
    return {
        "status": "success" if not failed else "partial",
        "registered": registered,
        "failed": failed,
        "total_in_registry": len(model_registry._models)
    }


@router.get("/discovered/search")
async def search_discovered(
    query: str = Query("", description="Search query"),
    provider: Optional[str] = None,
    capability: Optional[str] = None,
    max_cost: Optional[float] = None
):
    """Search discovered but not yet registered models"""
    
    return discovery_service.search(query, provider, capability, max_cost)


@router.get("/discovered/stats")
async def discovery_stats():
    """Get model discovery statistics"""
    
    return discovery_service.get_stats()