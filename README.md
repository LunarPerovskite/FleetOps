# FleetOps

> **The Operating System for Governed Human-Agent Work**

FleetOps is an open-source governance platform that connects your existing AI agents (Claude Code, Codex, Copilot, Cursor, Devin, etc.) with human oversight at every stage. Organizations maintain full control while agents handle the heavy lifting.

**Not just for customer service — for every team that uses AI agents:**
- 🏢 **Software Engineering** — Govern code generation, review, deployment
- 📊 **Data Science** — Manage model training, experiments, data pipelines  
- 🎨 **Creative Teams** — Oversee content generation, brand compliance
- 💼 **Operations** — Automate workflows with approval gates
- 📞 **Customer Service** — Multi-channel support with human handoff
- 🔬 **Research** — Manage literature reviews, experiment design
- 🏗️ **DevOps/SRE** — Infrastructure changes with approval workflows

![Status](https://img.shields.io/badge/status-beta-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18-blue)

## 🚀 What FleetOps Does

- **Human-in-the-Loop**: Insert human approval at any workflow stage
- **Agent Hierarchy**: Organize agents with customizable levels and unlimited sub-agents
- **Evidence Store**: Immutable, cryptographically signed audit trail
- **Provider Agnostic**: Choose your own stack (Clerk, Auth0, Okta, Supabase, AWS, etc.)
- **Multi-Channel**: Web, Slack, Discord, WhatsApp, Telegram, Email, Voice
- **Custom Dashboards**: Build personalized dashboards with drag-and-drop widgets
- **Audit Log**: Full event history with signature verification
- **API Keys**: Programmatic access with scoped permissions
- **Feature Flags**: Gradual rollouts and A/B testing
- **Slack/Discord Bots**: Interactive approval buttons and notifications
- **CLI Tool**: Command-line management (10 commands)
- **One-Click Deploy**: Vercel, Railway, Render deploy buttons
- **Webhooks**: Real-time event streaming with retry logic

## 🛡️ Competitive Moats

### What Makes FleetOps Different

FleetOps isn't just another agent tool — it's the **only governance layer** that works with whatever agents you already use.

**FleetOps vs OpenWork (desktop agent):**

| | **OpenWork** | **FleetOps** |
|---|---|---|
| **What it is** | Desktop app + chat UI | Governance/orchestration API layer |
| **Primary user** | Individual developers | Teams/enterprises with compliance needs |
| **UI** | Full desktop app | None (API-only, sits behind other UIs) |
| **Cost tracking** | ❌ Not mentioned | ✅ Real pricing from 10+ providers |
| **Budget enforcement** | ❌ No | ✅ Per-user, per-org limits |
| **Human approval** | ✅ Basic permissions | ✅ Async callbacks, stage-based, timeout |
| **Compliance rules** | ❌ No | ✅ Core feature |
| **Audit logging** | ✅ Basic audit trail | ✅ Structured JSON, trace IDs, security events |
| **Circuit breakers** | ❌ No | ✅ All LLM providers |
| **Rate limiting** | ❌ No | ✅ Redis-backed, per-user/org/IP |
| **Security headers** | ❌ No | ✅ HSTS, CSP, X-Frame-Options |
| **LLM providers** | 1-2 (OpenCode default) | 10+ (OpenAI, Anthropic, Gemini, Azure, Groq, etc.) |
| **IDE agents** | ❌ No | ✅ Claude Code, Roo Code adapters |
| **Multi-agent frameworks** | ❌ No | ✅ CrewAI, AutoGen, MetaGPT |
| **Metrics** | ❌ No | ✅ Prometheus endpoint |

**FleetOps vs Cursor/Copilot (coding agents):**
- Cursor/Copilot write code. FleetOps **governs** them.
- Cursor has no cost tracking. FleetOps tracks every token.
- Cursor has no approval workflows. FleetOps inserts approval gates.
- Cursor is single-user. FleetOps is multi-tenant with RBAC.

**FleetOps vs OpenWebUI (chat interface):**
- OpenWebUI is a chat UI. FleetOps sits **behind** it.
- OpenWebUI has basic cost tracking. FleetOps has real API pricing.
- OpenWebUI is single-server. FleetOps scales with Redis + PostgreSQL.

**FleetOps vs LangSmith (LLM observability):**
- LangSmith traces LLM calls. FleetOps **controls** them.
- LangSmith shows costs. FleetOps **enforces budgets**.
- LangSmith is cloud-only. FleetOps is self-hosted.

**FleetOps vs HumanLoop (human review):**
- HumanLoop adds human review. FleetOps adds **orchestration**.
- HumanLoop is for ML models. FleetOps is for **any agent**.
- HumanLoop is SaaS. FleetOps is open-source.

### Core Moats

#### 1. **Provider-Agnostic Governance**
Works with ANY LLM provider, IDE agent, or multi-agent framework. Not locked into one ecosystem.

#### 2. **Real Cost Tracking with API Pricing**
- Fetches actual pricing from OpenRouter, Groq, Together APIs
- Auto-discovers new models
- Tracks actual token usage from API responses (not estimates)
- Supports pay_per_token, subscription, free_local, aggregator pricing types

#### 3. **Budget Enforcement**
- Per-user, per-organization spending limits
- Hard stops when budget exceeded
- Alert thresholds (80%, 95%, 100%)
- Budget reset cycles (daily, weekly, monthly)

#### 4. **Production Hardening**
- Circuit breakers on all external LLM providers
- Redis-backed rate limiting (per-user, per-org, per-IP)
- Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- Request size limits
- Structured audit logging with trace IDs

#### 5. **Async Human Approval**
- Stage-based approval chains (operator → senior → director)
- Timeout handling (auto-approve, auto-reject, or escalate)
- Callback system for external systems
- WebSocket real-time updates

#### 6. **Multi-Agent Orchestration**
- Sequential, parallel, debate workflow modes
- Load balancing across providers
- Fallback when one provider fails
- CrewAI, AutoGen, MetaGPT integration

#### 7. **Compliance & Audit**
- Immutable audit trail (cryptographically signed)
- PII detection and redaction
- Data retention policies
- GDPR/SOC2-ready evidence chain

#### 8. **Observability**
- Prometheus metrics endpoint
- Request timing, token tracking, cost tracking
- Circuit breaker state monitoring
- Structured JSON logging

#### 9. **Extensibility**
- 20+ adapters (OpenAI, Anthropic, Gemini, Azure, Ollama, OpenWebUI, etc.)
- Plugin architecture for new providers
- Webhook system for real-time events
- CLI tool for automation

#### 10. **Self-Hosted by Default**
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

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           React Frontend                │
│  Dashboard | Tasks | Agents | Approvals │
└──────────────┬──────────────────────────┘
               │ WebSocket / HTTP
┌──────────────▼──────────────────────────┐
│           FastAPI Backend               │
│  Auth | Tasks | Agents | Events | WS    │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌─────────┐         ┌──────────┐
│PostgreSQL│         │  Redis   │
└─────────┘         └──────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Vite |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **Real-time** | WebSocket |
| **Auth** | JWT + Provider Adapters (Clerk, Auth0, Okta) |
| **Monitoring** | Sentry, Datadog, CloudWatch adapters |
| **Bots** | Slack SDK, Discord.py |
| **CLI** | Click (Python) |

## 📊 Stats

- **17 Frontend Pages** — All connected to real API
- **24 API Routes** — Full CRUD for all resources
- **18 Backend Services** — Task management, analytics, billing, webhooks
- **11 Provider Adapters** — Auth, DB, hosting, monitoring, secrets
- **9 Frontend Components** — Reusable UI building blocks
- **9 React Hooks** — State management, real-time, auth
- **6 Test Suites** — Backend, frontend, security, integration
- **75+ Git Commits** — Active development

## 🚦 Quick Start

### Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps

# Copy environment variables
cp .env.example .env
# Edit .env with your settings

# Validate your environment
python scripts/validate_env.py

# Start everything
docker-compose up -d

# Visit http://localhost:3000
```

### Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📋 Provider Configuration

FleetOps is provider-agnostic. Choose your stack:

```yaml
# Quick Start (Free)
auth: clerk
database: supabase
hosting: vercel
secrets: env
monitoring: sentry

# Enterprise
auth: okta
database: aws_rds
hosting: aws
secrets: vault
monitoring: datadog
```

Configure via UI at `/providers` or edit `fleetops.yaml`.

## 💼 Use Cases

### Software Engineering Teams
- **Code Generation**: Claude Code generates code → human review → approval → merge
- **Code Review**: Copilot suggests changes → senior dev approves → merge
- **Infrastructure**: Terraform plans → SRE approval → apply
- **Deployments**: CI/CD pipeline → approval gate → production deploy
- **Bug Triage**: AI categorizes bugs → team lead approves priority → assign
- **Documentation**: AI generates docs → technical writer reviews → publish

### Data Science Teams
- **Experiment Management**: AI runs experiments → data scientist reviews → publish results
- **Model Training**: Training jobs → monitoring → human evaluation → deploy
- **Data Pipelines**: ETL processes → data quality checks → approval → schedule

### Creative/Content Teams
- **Content Generation**: AI drafts content → editor reviews → brand check → publish
- **Video Production**: AI generates scripts → director approves → production
- **Marketing Campaigns**: AI creates campaigns → marketing lead approves → launch

### Operations Teams
- **Workflow Automation**: AI processes tickets → human review → resolution
- **Document Processing**: AI extracts data → verification → approval → record
- **Quality Assurance**: AI runs tests → QA review → approval → release

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# Environment validation
python scripts/validate_env.py
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 💬 Community

- [Discord](https://discord.gg/fleetops) (coming soon)
- [Telegram](https://t.me/fleetops) (coming soon)
- [GitHub Discussions](https://github.com/LunarPerovskite/FleetOps/discussions)

## 🙏 Acknowledgments

Built with ❤️ by the FleetOps team and contributors.

## 📞 Contact

- **Founder**: Juan Esteban Mosquera
- **Email**: juanestebanmosquera@yahoo.com
- **GitHub**: [@LunarPerovskite](https://github.com/LunarPerovskite)
