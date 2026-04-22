# FleetOps Architecture Vision

## Core Philosophy

**FleetOps is NOT a chat UI.** It's the governance, compliance, cost management, and orchestration layer that sits BEHIND whatever UI or agents you use.

```
┌─────────────────────────────────────────────────────────────┐
│                     USER FACES (Any UI)                     │
├─────────────────────────────────────────────────────────────┤
│  OpenWebUI  │  Claude Code  │  Roo Code  │  Custom Chat   │
│  (Chat)     │  (CLI)        │  (VS Code) │  (Your App)    │
└──────┬──────┴───────┬───────┴─────┬──────┴──────┬─────────┘
       │              │             │             │
       └──────────────┴──────┬──────┴─────────────┘
                             │
              ┌──────────────▼──────────────┐
              │        FleetOps Core        │
              │  ┌─────────────────────┐    │
              │  │  Human Approval     │    │
              │  │  Cost Tracking      │    │
              │  │  Budget Enforcement │    │
              │  │  Audit Logging      │    │
              │  │  Agent Orchestration│    │
              │  │  Compliance Rules   │    │
              │  └─────────────────────┘    │
              └──────────────┬──────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐  ┌───────────▼────────┐  ┌────────▼─────┐
│   Local     │  │     Cloud        │  │  Aggregator  │
│   LLMs      │  │     LLMs         │  │              │
│             │  │                  │  │              │
│ Ollama      │  │ OpenAI GPT-4     │  │ OpenRouter   │
│ vLLM        │  │ Anthropic Claude │  │ Together     │
│ TGI         │  │ Google Gemini    │  │ Groq         │
│ Local       │  │ Azure OpenAI     │  │ Perplexity   │
└─────────────┘  └──────────────────┘  └──────────────┘
```

## What FleetOps Does

### 1. **Governance Layer** ✅
- Human approval before expensive actions
- Model approval/rejection per user/team
- Approval chains (operator → senior → director)

### 2. **Cost Management** ✅
- Real usage extraction from API responses
- Dynamic pricing from provider APIs
- Budget enforcement (stop at $5)
- Cost reports by user/team/agent

### 3. **Compliance** ✅
- Audit trail (every request logged)
- Immutable evidence chain
- PII detection and redaction
- Data retention policies

### 4. **Agent Orchestration** ✅
- Multi-agent workflows
- Sequential, parallel, debate modes
- Load balancing across providers
- Fallback when one fails

### 5. **Integration Hub** ✅
- 20+ adapters: OpenAI, Anthropic, Gemini, Azure, Ollama, OpenWebUI, etc.
- Any agent: CrewAI, AutoGen, MetaGPT, Claude Code, Roo Code, etc.
- Any deployment: Local, VPS, Docker, Kubernetes

## What FleetOps Does NOT Do

- **Chat interface** → Use OpenWebUI, Claude Code, etc.
- **Run models** → Use Ollama, vLLM, cloud APIs
- **Write code** → Use Cursor, Aider, Roo Code, etc.

FleetOps **coordinates** and **governs** these tools.

## Use Cases

### Case 1: Team Using OpenWebUI
```
User → OpenWebUI → FleetOps → Ollama
                         ↓
                    Tracks cost
                    Checks budget
                    Logs audit trail
```

### Case 2: Developer Using Roo Code
```
Dev → Roo Code → FleetOps → OpenRouter → Claude
                      ↓
                 Requires approval for $5+ requests
                 Tracks token usage
                 Logs all changes
```

### Case 3: Multi-Agent Workflow
```
Task → FleetOps → CrewAI (research)
              ↓
         FleetOps → AutoGen (analysis)
              ↓
         FleetOps → Claude Code (implementation)
              ↓
         Human approval → Deploy
```

## Deployment Options

```yaml
# Option 1: All local
services:
  fleetops:
    build: ./backend
  openwebui:
    image: open-webui
  ollama:
    image: ollama/ollama

# Option 2: Mixed
services:
  fleetops:
    build: ./backend
  # OpenWebUI on VPS
  # Claude Code on laptop
  # GPT-4 via API

# Option 3: All remote
- FleetOps on VPS
- Ollama on GPU server
- OpenAI for fast tasks
```

## Configuration

```bash
# Core
FLEETOPS_URL=http://localhost:8000

# Local LLM
OLLAMA_URL=http://localhost:11434  # or https://my-vps.com:11434

# Cloud LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# UI
OPENWEBUI_URL=http://localhost:8080

# Agents
CLAUDE_CODE_CLI=claude
ROO_CODE_CLI=roo
AIDER_CLI=aider

# Cost tracking
ENABLE_COST_TRACKING=true
DEFAULT_BUDGET_USD=5.00
```

## Status

✅ **Done:**
- 20+ adapters (OpenAI, Anthropic, Gemini, Azure, Ollama, OpenWebUI, etc.)
- Real usage extraction
- Dynamic pricing
- Cost tracking
- Budget alerts
- Audit logging
- Security framework

🔄 **In Progress:**
- Frontend UI for compliance dashboards
- Database migrations
- API route wiring

⏳ **Pending:**
- Human approval UI
- Cost reports frontend
- Model governance UI
- Tests
