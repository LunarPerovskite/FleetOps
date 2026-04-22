"""OpenWebUI API Routes for FleetOps

Expose OpenWebUI functionality through FleetOps with governance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.core.auth import get_current_user
from app.models.models import User
from app.adapters.openwebui_adapter import openwebui_adapter

router = APIRouter(prefix="/openwebui", tags=["OpenWebUI"])


@router.get("/health")
async def health_check(current_user: User = Depends(get_current_user)):
    """Check OpenWebUI connection"""
    return await openwebui_adapter.health_check()


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    """List all models available in OpenWebUI/Ollama"""
    try:
        models = await openwebui_adapter.list_models()
        return {
            "status": "success",
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/pull")
async def pull_model(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """Pull/download a model into Ollama"""
    try:
        result = await openwebui_adapter.pull_model(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(
    message: str,
    model: str = Query("llama3.1:8b", description="Model to use"),
    task_id: Optional[str] = Query(None, description="FleetOps task ID"),
    system_prompt: Optional[str] = Query(None, description="System prompt"),
    current_user: User = Depends(get_current_user)
):
    """Chat through OpenWebUI with cost tracking
    
    Example:
        POST /api/v1/openwebui/chat
        ?message=Hello&model=llama3.1:8b&task_id=task_123
    """
    try:
        result = await openwebui_adapter.chat(
            message=message,
            task_id=task_id or f"chat_{current_user.id}_{datetime.utcnow().timestamp()}",
            model=model,
            system_prompt=system_prompt,
            user_id=current_user.id
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/history")
async def chat_with_history(
    messages: List[dict],
    model: str = Query("llama3.1:8b"),
    task_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Chat with conversation history (multi-turn)"""
    try:
        result = await openwebui_adapter.chat_with_history(
            messages=messages,
            task_id=task_id or f"chat_history_{current_user.id}",
            model=model,
            user_id=current_user.id
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user)
):
    """Get user's conversation history"""
    try:
        conversations = await openwebui_adapter.get_conversations(
            user_id=current_user.id
        )
        return {
            "status": "success",
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{chat_id}")
async def get_conversation(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation"""
    try:
        conversation = await openwebui_adapter.get_conversation(chat_id)
        return {
            "status": "success",
            "conversation": conversation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/title")
async def generate_title(
    message: str,
    model: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Generate a title for a conversation"""
    try:
        result = await openwebui_adapter.generate_title(message, model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from datetime import datetime
