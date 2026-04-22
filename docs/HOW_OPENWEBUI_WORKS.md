# How OpenWebUI Works (And How FleetOps Connects)

## What is OpenWebUI?

OpenWebUI is a **self-hosted web interface** for talking to AI models. Think of it like ChatGPT, but:
- **You own it** - runs on your server
- **Any model** - works with Ollama, OpenAI, Anthropic, etc.
- **Multi-user** - teams can share
- **Extensible** - plugins, pipelines, RAG

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Browser  │────▶│   OpenWebUI     │────▶│   Ollama API   │
│  (Chat interface)│    │  (Web server)   │     │  (LLM runner)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              │  OR
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │  (Cloud LLM)    │
                       └─────────────────┘
```

## How It Works (Step by Step)

### 1. User Types a Message
```javascript
// Frontend sends to OpenWebUI backend
POST /api/chat/completions
{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

### 2. OpenWebUI Forwards to LLM
```python
# OpenWebUI backend forwards to Ollama
POST http://ollama:11434/api/generate
{
  "model": "llama3.1:8b",
  "prompt": "Hello!",
  "stream": false
}
```

### 3. LLM Responds
```json
{
  "model": "llama3.1:8b",
  "response": "Hello! How can I help you today?",
  "done": true,
  "total_duration": 1234567890
}
```

### 4. OpenWebUI Returns to User
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  }],
  "model": "llama3.1:8b"
}
```

## Key Features

### 1. Model Management
```bash
# List models
curl http://localhost:11434/api/tags

# Pull new model
curl http://localhost:11434/api/pull -d '{"name": "llama3.1"}'
```

### 2. Chat History
```python
# OpenWebUI stores in SQLite/PostgreSQL
# Table: chat
# Columns: id, user_id, title, messages(JSON)
```

### 3. RAG (Document Upload)
```python
# User uploads PDF
# OpenWebUI chunks it, embeds it, stores in vector DB
# When user asks, retrieves relevant chunks
```

### 4. Pipelines (Functions)
```python
# Custom processing before/after LLM call
class ExamplePipeline:
    async def inlet(self, body, user):
        # Modify request before sending to LLM
        body["messages"][0]["content"] += "\nBe concise."
        return body
    
    async def outlet(self, body, user):
        # Modify response before showing user
        return body
```

## How FleetOps Integrates

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    User      │────▶│  FleetOps    │────▶│  OpenWebUI   │────▶│   Ollama     │
│              │     │  (Governance)│     │  (UI/API)    │     │  (LLM)       │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │
                            │ (or directly)
                            ▼
                     ┌──────────────┐
                     │   OpenAI     │
                     │  (API Key)   │
                     └──────────────┘
```

### Integration Points

1. **FleetOps manages OpenWebUI**
   - Start/stop models
   - Set which models are allowed
   - Monitor usage

2. **FleetOps adds governance**
   - Human approval for expensive models
   - Budget limits
   - Audit logging

3. **OpenWebUI uses FleetOps backend**
   - Instead of Ollama directly, calls FleetOps
   - FleetOps decides which LLM to use
   - FleetOps tracks costs

## Code Example: FleetOps → OpenWebUI

```python
import httpx

class OpenWebUIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def chat(self, message, model="llama3.1:8b"):
        # Call OpenWebUI API
        response = await self.client.post("/api/chat/completions", json={
            "model": model,
            "messages": [{"role": "user", "content": message}]
        })
        return response.json()
    
    async def list_models(self):
        # Get available models
        response = await self.client.get("/api/models")
        return response.json()
```

## Why This Matters for FleetOps

1. **Users already know OpenWebUI** - familiar interface
2. **FleetOps adds the business layer**:
   - Cost tracking
   - Approval workflows
   - Multi-agent orchestration
   - Audit trails

3. **Best of both worlds**:
   - Easy chat interface (OpenWebUI)
   - Enterprise governance (FleetOps)
