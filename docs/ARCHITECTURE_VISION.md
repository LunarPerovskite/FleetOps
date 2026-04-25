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

## Competitive Moats

### 1. Provider-Agnostic Governance
Works with ANY LLM provider, IDE agent, or multi-agent framework. Not locked into one ecosystem.

### 2. Real Cost Tracking with API Pricing
- Fetches actual pricing from OpenRouter, Groq, Together APIs
- Auto-discovers new models
- Tracks actual token usage from API responses (not estimates)
- Supports pay_per_token, subscription, free_local, aggregator pricing types

### 3. Budget Enforcement
- Per-user, per-organization spending limits
- Hard stops when budget exceeded
- Alert thresholds (80%, 95%, 100%)
- Budget reset cycles (daily, weekly, monthly)

### 4. Production Hardening
- Circuit breakers on all external LLM providers
- Redis-backed rate limiting (per-user, per-org, per-IP)
- Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- Request size limits
- Structured audit logging with trace IDs

### 5. Async Human Approval
- Stage-based approval chains (operator → senior → director)
- Timeout handling (auto-approve, auto-reject, or escalate)
- Callback system for external systems
- WebSocket real-time updates

### 6. Multi-Agent Orchestration
- Sequential, parallel, debate workflow modes
- Load balancing across providers
- Fallback when one provider fails
- CrewAI, AutoGen, MetaGPT integration

### 7. Compliance & Audit
- Immutable audit trail (cryptographically signed)
- PII detection and redaction
- Data retention policies
- GDPR/SOC2-ready evidence chain

### 8. Observability
- Prometheus metrics endpoint
- Request timing, token tracking, cost tracking
- Circuit breaker state monitoring
- Structured JSON logging

### 9. Extensibility
- 20+ adapters (OpenAI, Anthropic, Gemini, Azure, Ollama, OpenWebUI, etc.)
- Plugin architecture for new providers
- Webhook system for real-time events
- CLI tool for automation

### 10. Self-Hosted by Default
- Your data stays on your infrastructure
- No vendor lock-in
- No per-seat pricing
- Full source code access (MIT license)

### Why These Moats Matter

**For Enterprises:**
- Budget control prevents AI overspend
- Audit trails satisfy compliance requirements
- Approval workflows prevent unauthorized changes
- Self-hosted = data sovereignty

**For Teams:**
- Cost transparency across all AI usage
- No surprise bills at month-end
- Governance without slowing down developers
- Works with existing tools (no migration)

**For Developers:**
- Use any agent framework you want
- Switch LLM providers without changing code
- Track costs per project/agent
- Local development with same governance
