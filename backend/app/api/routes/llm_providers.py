"""LLM Provider API Routes for FleetOps

Chat with OpenAI, Anthropic, Gemini, Azure directly through FleetOps.
All with real usage tracking and cost management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List

from app.core.auth import get_current_user
from app.models.models import User
from app.adapters.llm_providers import (
    openai_adapter, anthropic_adapter, 
    gemini_adapter, azure_adapter
)

router = APIRouter(prefix="/llm", tags=["LLM Providers"])


@router.post("/chat/{provider}")
async def chat_with_provider(
    provider: str,  # openai, anthropic, gemini, azure
    messages: List[dict],
    task_id: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    current_user: User = Depends(get_current_user)
):
    """Chat with any LLM provider through FleetOps
    
    Examples:
        POST /api/v1/llm/chat/openai
        {
            "messages": [{"role": "user", "content": "Hello!"}],
            "task_id": "task_123",
            "model": "gpt-4o"
        }
        
        POST /api/v1/llm/chat/anthropic
        {
            "messages": [{"role": "user", "content": "Hello!"}],
            "task_id": "task_124",
            "model": "claude-3-5-sonnet-20241022"
        }
    """
    try:
        provider = provider.lower()
        
        if provider == "openai":
            result = await openai_adapter.chat(
                messages=messages,
                task_id=task_id,
                model=model,
                temperature=temperature,
                user_id=current_user.id
            )
        elif provider == "anthropic":
            result = await anthropic_adapter.chat(
                messages=messages,
                task_id=task_id,
                model=model,
                user_id=current_user.id
            )
        elif provider == "gemini":
            result = await gemini_adapter.chat(
                messages=messages,
                task_id=task_id,
                model=model,
                user_id=current_user.id
            )
        elif provider == "azure":
            result = await azure_adapter.chat(
                messages=messages,
                task_id=task_id,
                deployment=model,
                user_id=current_user.id
            )
        else:
            raise HTTPException(status_code=400, detail=f"Provider '{provider}' not supported")
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{provider}")
async def list_provider_models(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """List available models for a provider"""
    try:
        if provider == "openai":
            models = await openai_adapter.list_models()
        else:
            # Return known models for other providers
            models = {
                "anthropic": [
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
                ],
                "gemini": [
                    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
                    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
                    {"id": "gemini-pro", "name": "Gemini Pro"},
                ],
                "azure": [
                    {"id": "gpt-4", "name": "GPT-4"},
                    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                    {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo"},
                ]
            }.get(provider, [])
        
        return {
            "status": "success",
            "provider": provider,
            "models": models
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
