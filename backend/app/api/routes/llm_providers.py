"""LLM Provider API Routes for FleetOps

Direct API access to all supported LLM providers with FleetOps governance:
- Cost tracking on every request
- Usage extraction from real API responses
- Circuit breaker protection
- Audit logging

Providers: OpenAI, Anthropic, Google Gemini, Azure OpenAI, Mistral, Cohere
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.auth import verify_token
from app.core.logging_config import get_logger, log_provider_call
from app.core.metrics import metrics
from app.adapters.llm_providers import (
    OpenAIAdapter, AnthropicAdapter, GeminiAdapter, 
    AzureOpenAIAdapter, UnifiedLLMChatAdapter
)

logger = get_logger("fleetops.api.llm_providers")
router = APIRouter()


# ─── Pydantic Models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for chat completions"""
    messages: List[Dict[str, str]] = Field(
        ...,
        description="List of messages in OpenAI format",
        example=[{"role": "user", "content": "Hello, how are you?"}]
    )
    model: Optional[str] = Field(
        None,
        description="Model ID (e.g., 'gpt-4o', 'claude-3-5-sonnet')"
    )
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0-2)"
    )
    max_tokens: int = Field(
        2048,
        ge=1,
        le=8192,
        description="Maximum tokens to generate"
    )
    task_id: str = Field(
        ...,
        description="FleetOps task ID for tracking and governance"
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID for audit trail"
    )


class ChatResponse(BaseModel):
    """Response from chat completion"""
    status: str = Field(..., description="success or error")
    content: Optional[str] = Field(None, description="Generated content")
    model: Optional[str] = Field(None, description="Model used")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage")
    cost_usd: Optional[str] = Field(None, description="Cost in USD")
    pricing_source: Optional[str] = Field(None, description="pricing_source")
    error: Optional[str] = Field(None, description="Error message if failed")


class ModelInfo(BaseModel):
    """Information about an available model"""
    id: str
    name: str
    owned_by: Optional[str] = None


class ProviderStatus(BaseModel):
    """Provider health status"""
    provider: str
    status: str
    models_available: int
    circuit_breaker_state: str


# ─── Routes ─────────────────────────────────────────────────────────────

@router.post(
    "/chat/openai",
    response_model=ChatResponse,
    summary="Chat with OpenAI",
    description="""
    Send a chat request to OpenAI through FleetOps.
    
    FleetOps handles:
    - Cost tracking with dynamic pricing
    - Real token usage extraction
    - Circuit breaker protection
    - Audit logging
    
    Requires OpenAI API key configured in environment.
    """,
    response_description="Generated response with usage and cost",
    tags=["llm-providers"]
)
async def chat_openai(
    request: ChatRequest,
    current_user: Dict = Depends(verify_token)
):
    """Chat via OpenAI with FleetOps governance"""
    adapter = OpenAIAdapter()
    try:
        result = await adapter.chat(
            messages=request.messages,
            task_id=request.task_id,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            user_id=request.user_id or current_user.get("id")
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}", extra={"task_id": request.task_id})
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await adapter.close()


@router.post(
    "/chat/anthropic",
    response_model=ChatResponse,
    summary="Chat with Anthropic Claude",
    description="""
    Send a chat request to Anthropic Claude through FleetOps.
    
    Supports Claude 3 Opus, Sonnet, and Haiku models.
    All requests are tracked for cost and compliance.
    """,
    tags=["llm-providers"]
)
async def chat_anthropic(
    request: ChatRequest,
    current_user: Dict = Depends(verify_token)
):
    """Chat via Anthropic with FleetOps governance"""
    adapter = AnthropicAdapter()
    try:
        result = await adapter.chat(
            messages=request.messages,
            task_id=request.task_id,
            model=request.model,
            max_tokens=request.max_tokens,
            user_id=request.user_id or current_user.get("id")
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Anthropic chat error: {e}", extra={"task_id": request.task_id})
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await adapter.close()


@router.post(
    "/chat/gemini",
    response_model=ChatResponse,
    summary="Chat with Google Gemini",
    description="Send a chat request to Google Gemini through FleetOps.",
    tags=["llm-providers"]
)
async def chat_gemini(
    request: ChatRequest,
    current_user: Dict = Depends(verify_token)
):
    """Chat via Google Gemini with FleetOps governance"""
    adapter = GeminiAdapter()
    try:
        result = await adapter.chat(
            messages=request.messages,
            task_id=request.task_id,
            model=request.model,
            user_id=request.user_id or current_user.get("id")
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Gemini chat error: {e}", extra={"task_id": request.task_id})
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await adapter.close()


@router.post(
    "/chat/azure",
    response_model=ChatResponse,
    summary="Chat with Azure OpenAI",
    description="Send a chat request to Azure OpenAI deployment through FleetOps.",
    tags=["llm-providers"]
)
async def chat_azure(
    request: ChatRequest,
    deployment: Optional[str] = Query(None, description="Azure deployment name"),
    current_user: Dict = Depends(verify_token)
):
    """Chat via Azure OpenAI with FleetOps governance"""
    adapter = AzureOpenAIAdapter()
    try:
        result = await adapter.chat(
            messages=request.messages,
            task_id=request.task_id,
            deployment=deployment,
            user_id=request.user_id or current_user.get("id")
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Azure chat error: {e}", extra={"task_id": request.task_id})
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await adapter.close()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with any provider (auto-routed)",
    description="""
    Unified chat endpoint that auto-routes to the best provider.
    
    Provider selection criteria (in order):
    1. User-specified provider
    2. Cost-optimized (cheapest for token count)
    3. Speed-optimized (lowest latency)
    4. Quality-optimized (best model for task)
    
    All requests are tracked for cost and compliance.
    """,
    tags=["llm-providers"]
)
async def chat_unified(
    request: ChatRequest,
    provider: Optional[str] = Query(None, description="Force specific provider"),
    strategy: str = Query("balanced", description="Routing strategy: balanced, cost, speed, quality"),
    current_user: Dict = Depends(verify_token)
):
    """Chat via auto-selected provider with FleetOps governance"""
    adapter = UnifiedLLMChatAdapter()
    try:
        result = await adapter.chat(
            messages=request.messages,
            task_id=request.task_id,
            model=request.model,
            provider=provider,
            strategy=strategy,
            user_id=request.user_id or current_user.get("id")
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Unified chat error: {e}", extra={"task_id": request.task_id})
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await adapter.close()


@router.get(
    "/providers",
    response_model=List[ProviderStatus],
    summary="List all LLM providers",
    description="Get status of all configured LLM providers including health and available models.",
    tags=["llm-providers"]
)
async def list_providers():
    """List all configured LLM providers with their status"""
    providers = []
    
    # Check each provider
    for name, adapter_class in [
        ("openai", OpenAIAdapter),
        ("anthropic", AnthropicAdapter),
        ("gemini", GeminiAdapter),
        ("azure", AzureOpenAIAdapter),
    ]:
        try:
            adapter = adapter_class()
            models = await adapter.list_models()
            # Get circuit breaker state
            from app.core.circuit_breaker import CircuitBreaker
            cb = CircuitBreaker._instances.get(name)
            cb_state = cb.state.name if cb else "CLOSED"
            
            providers.append({
                "provider": name,
                "status": "healthy" if models and not any("error" in str(m) for m in models) else "error",
                "models_available": len([m for m in models if "error" not in str(m)]),
                "circuit_breaker_state": cb_state
            })
            await adapter.close()
        except Exception as e:
            providers.append({
                "provider": name,
                "status": f"error: {str(e)}",
                "models_available": 0,
                "circuit_breaker_state": "OPEN"
            })
    
    return providers


@router.get(
    "/providers/{provider}/models",
    response_model=List[ModelInfo],
    summary="List models for a provider",
    description="Get all available models for a specific LLM provider.",
    tags=["llm-providers"]
)
async def list_provider_models(provider: str):
    """List available models for a specific provider"""
    adapter_map = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "gemini": GeminiAdapter,
        "azure": AzureOpenAIAdapter,
    }
    
    adapter_class = adapter_map.get(provider)
    if not adapter_class:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    
    adapter = adapter_class()
    try:
        models = await adapter.list_models()
        return [ModelInfo(**m) for m in models if "error" not in str(m)]
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await adapter.close()
