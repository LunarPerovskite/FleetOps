# OpenWebUI Integration Guide

OpenWebUI is a popular self-hosted web interface for LLMs (like Ollama). Here's how to integrate it with FleetOps.

## What is OpenWebUI?

- **Web interface** for chatting with local LLMs (Ollama, etc.)
- **Multi-user** support with auth
- **Model management** (download, switch models)
- **RAG support** (upload documents)
- **Pipelines** (pre/post processing)
- **API endpoints** for programmatic access

## Integration Methods

### Method 1: FleetOps as OpenWebUI Backend (Recommended)

FleetOps manages all AI services, OpenWebUI is the chat interface.

```yaml
# docker-compose.yml
services:
  fleetops-backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - OPENWEBUI_URL=http://openwebui:8080
    
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - ENABLE_SIGNUP=true
      - DEFAULT_MODELS=llama3.1:8b
    volumes:
      - openwebui-data:/app/backend/data
    
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-models:/root/.ollama

volumes:
  openwebui-data:
  ollama-models:
```

### Method 2: FleetOps Governs OpenWebUI

OpenWebUI runs independently, FleetOps monitors and controls it.

```python
# FleetOps adapter for OpenWebUI
class OpenWebUIAdapter:
    """FleetOps adapter for OpenWebUI
    
    Features:
    - List available models in OpenWebUI
    - Send chat requests through OpenWebUI API
    - Monitor token usage
    - Track costs
    - Human approval for expensive models
    """
    
    def __init__(self):
        self.base_url = os.getenv("OPENWEBUI_URL", "http://localhost:8080")
        self.api_key = os.getenv("OPENWEBUI_API_KEY", "")
        
    async def list_models(self) -> List[Dict]:
        """Get models available in OpenWebUI"""
        response = await self.client.get("/api/models")
        return response.json()
    
    async def chat(self, message: str, model: str, task_id: str) -> Dict:
        """Chat through OpenWebUI with governance"""
        
        # Check if model is allowed
        if not await self.is_model_allowed(model):
            return {"status": "rejected", "reason": "Model not approved"}
        
        # Check budget
        cost_estimate = await self.estimate_cost(model, message)
        if not await self.check_budget(task_id, cost_estimate):
            return {"status": "rejected", "reason": "Budget exceeded"}
        
        # Send request
        response = await self.client.post("/api/chat/completions", json={
            "model": model,
            "messages": [{"role": "user", "content": message}]
        })
        
        # Track real usage
        usage = await RealUsageExtractor.extract_openwebui_usage(response.json())
        await cost_tracker.track_usage(
            service="openwebui",
            model=model,
            agent_id="openwebui_adapter",
            task_id=task_id,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"]
        )
        
        return response.json()
```

## Setup Steps

### 1. Install OpenWebUI

```bash
# Docker (recommended)
docker run -d -p 8080:8080 \
  -v openwebui:/app/backend/data \
  --name openwebui \
  ghcr.io/open-webui/open-webui:main

# Or with Ollama
docker run -d -p 8080:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v openwebui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ghcr.io/open-webui/open-webui:main
```

### 2. Configure FleetOps

Add to `.env`:
```bash
# OpenWebUI
OPENWEBUI_URL=http://localhost:8080
OPENWEBUI_API_KEY=your-api-key

# Ollama (if using)
OLLAMA_URL=http://localhost:11434
```

### 3. Create Adapter

```python
# backend/app/adapters/openwebui_adapter.py
import os
import httpx
from typing import Dict, Any, List

from app.core.usage_extraction import RealUsageExtractor
from app.core.cost_tracking import cost_tracker

class OpenWebUIAdapter:
    """FleetOps adapter for OpenWebUI"""
    
    def __init__(self):
        self.base_url = os.getenv("OPENWEBUI_URL", "http://localhost:8080")
        self.api_key = os.getenv("OPENWEBUI_API_KEY", "")
        self.timeout = 120
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10)
        )
    
    async def list_models(self) -> List[Dict]:
        """List models available in OpenWebUI"""
        try:
            response = await self.client.get("/api/models")
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "size": model.get("size"),
                    "owned_by": model.get("owned_by")
                }
                for model in data.get("data", [])
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    async def chat(self, message: str, model: str, task_id: str,
                  user_id: str = None) -> Dict[str, Any]:
        """Chat through OpenWebUI"""
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
            
            response = await self.client.post("/api/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract usage
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Track cost
            cost_result = await cost_tracker.track_usage(
                service="openwebui",
                model=model,
                agent_id="openwebui_adapter",
                task_id=task_id,
                user_id=user_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            return {
                "status": "success",
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_result["cost_usd"]
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_conversations(self) -> List[Dict]:
        """Get conversation history"""
        try:
            response = await self.client.get("/api/chats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return [{"error": str(e)}]
    
    async def close(self):
        await self.client.aclose()


openwebui_adapter = OpenWebUIAdapter()
```

### 4. Add to FleetOps Registry

```python
# In backend/app/adapters/all_adapters.py
"openwebui": {
    "name": "OpenWebUI",
    "category": "ui",
    "adapter": "openwebui_adapter",
    "supports_governance": True,
    "url_env": "OPENWEBUI_URL",
    "description": "Self-hosted web UI for LLMs"
}
```

### 5. API Routes

```python
# backend/app/api/routes/openwebui.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.adapters.openwebui_adapter import openwebui_adapter

router = APIRouter(prefix="/openwebui", tags=["OpenWebUI"])

@router.get("/models")
async def list_models(current_user = Depends(get_current_user)):
    """List OpenWebUI models"""
    return await openwebui_adapter.list_models()

@router.post("/chat")
async def chat(
    message: str,
    model: str = "llama3.1:8b",
    task_id: str = None,
    current_user = Depends(get_current_user)
):
    """Chat through OpenWebUI with cost tracking"""
    return await openwebui_adapter.chat(
        message=message,
        model=model,
        task_id=task_id or f"chat_{current_user.id}",
        user_id=current_user.id
    )
```

## Features

### Cost Tracking
- Tracks every request cost
- Budget alerts
- Usage per user

### Model Governance
- Approve/reject models
- Usage limits per model
- Audit logs

### Integration with Other Agents
- Roo Code can use OpenWebUI as backend
- Claude Code can query OpenWebUI models
- Any agent can chat through OpenWebUI

## Advanced: Pipeline Integration

OpenWebUI supports pipelines (functions that process requests):

```python
# Pipeline that routes through FleetOps
class FleetOpsPipeline:
    """OpenWebUI pipeline that sends requests to FleetOps for approval"""
    
    async def inlet(self, body: dict, user: dict) -> dict:
        # Before request - check with FleetOps
        approval = await self.check_with_fleetops(body)
        if not approval["approved"]:
            raise Exception(f"Request blocked: {approval['reason']}")
        return body
    
    async def outlet(self, body: dict, user: dict) -> dict:
        # After request - log to FleetOps
        await self.log_to_fleetops(body)
        return body
```

## Deployment

```bash
# Start everything
docker-compose up -d

# FleetOps: http://localhost:8000
# OpenWebUI: http://localhost:8080
# Ollama API: http://localhost:11434
```

## Next Steps

1. Install OpenWebUI
2. Configure FleetOps adapter
3. Test chat with cost tracking
4. Set up model governance
5. Add pipelines for advanced control
