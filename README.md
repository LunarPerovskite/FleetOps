# FleetOps

> **The Operating System for Governed Human-Agent Work**

FleetOps is an open-source governance platform that connects your existing AI agents (Claude Code, Codex, Copilot, Cursor, Devin, etc.) with human oversight at every stage. Organizations maintain full control while agents handle the heavy lifting.

**Built for every team that uses AI agents:**
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

- **Human-in-the-Loop** — Insert human approval at any workflow stage
- **Agent Hierarchy** — Organize agents with customizable levels and unlimited sub-agents
- **Cost Tracking** — Real-time budget monitoring with per-agent attribution
- **Budget Enforcement** — Hard stops when budgets are exceeded
- **Evidence Store** — Immutable, cryptographically signed audit trail
- **Provider Agnostic** — Choose your own stack (Clerk, Auth0, Okta, Supabase, AWS, etc.)
- **Multi-Channel** — Web, Slack, Discord, WhatsApp, Telegram, Email, Voice
- **Custom Dashboards** — Build personalized dashboards with drag-and-drop widgets
- **Audit Log** — Full event history with signature verification
- **API Keys** — Programmatic access with scoped permissions
- **Feature Flags** — Gradual rollouts and A/B testing
- **Slack/Discord Bots** — Interactive approval buttons and notifications
- **CLI Tool** — Command-line management with colorful output
- **Python Client Library** — `fleetops-cli` package for programmatic access
- **MCP Server** — Model Context Protocol for any MCP-compatible agent
- **One-Click Deploy** — Vercel, Railway, Render deploy buttons
- **Webhooks** — Real-time event streaming with retry logic
- **Multi-Agent Swarms** — Orchestrate agent collectives with cost roll-up
- **Circuit Breakers** — Automatic fallback when LLM providers fail
- **Rate Limiting** — Redis-backed per-user and per-org limits
- **Danger Detection** — Automatic risk scoring for agent actions
- **Hierarchy Escalation** — Escalate approvals to managers based on risk
- **Usage Extraction** — Automatic token/usage tracking across all LLM providers
- **Media Generation** — Cost tracking for DALL-E, Runway, ElevenLabs
- **Connection Layer** — Provider-agnostic LLM connection management

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           React Frontend                │
│  Dashboard | Tasks | Agents | Approvals │
│  Analytics | LLM Usage | Search | Orgs  │
└──────────────┬──────────────────────────┘
               │ WebSocket / HTTP
┌──────────────▼──────────────────────────┐
│           FastAPI Backend               │
│  Auth | Tasks | Agents | Events | WS    │
│  Billing | Hierarchy | Audit | Search   │
│  Cost Tracking | Circuit Breakers       │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌─────────┐         ┌──────────┐
│PostgreSQL│         │  Redis   │
└─────────┘         └──────────┘
    │
    ▼
┌─────────────┐   ┌──────────────┐
│ CLI Tool    │   │ MCP Server   │
│ Client Lib  │   │ (MCP agents) │
└─────────────┘   └──────────────┘
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
| **Client Library** | `fleetops-cli` (async/sync Python) |
| **MCP** | Model Context Protocol server |

## 📊 Stats

- **22 Frontend Pages** — All connected to real API
- **24 API Routes** — Full CRUD for all resources
- **18+ Backend Services** — Task management, analytics, billing, webhooks, circuit breakers, rate limiting, cost tracking
- **20+ Provider Adapters** — Auth, DB, hosting, monitoring, secrets, LLM providers, media generation
- **12 Frontend Components** — Reusable UI building blocks
- **9 React Hooks** — State management, real-time, auth
- **216+ Unit Tests** — Full backend test coverage with CI/CD
- **135+ Git Commits** — Active development

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
- **Code Generation** — AI generates code → human review → approval → merge
- **Code Review** — AI suggests changes → senior dev approves → merge
- **Infrastructure** — Terraform plans → SRE approval → apply
- **Deployments** — CI/CD pipeline → approval gate → production deploy
- **Bug Triage** — AI categorizes bugs → team lead approves priority → assign

### Data Science Teams
- **Experiment Management** — AI runs experiments → data scientist reviews → publish results
- **Model Training** — Training jobs → monitoring → human evaluation → deploy
- **Data Pipelines** — ETL processes → data quality checks → approval → schedule

### Creative/Content Teams
- **Content Generation** — AI drafts content → editor reviews → brand check → publish
- **Video Production** — AI generates scripts → director approves → production
- **Marketing Campaigns** — AI creates campaigns → marketing lead approves → launch

### Operations Teams
- **Workflow Automation** — AI processes tickets → human review → resolution
- **Document Processing** — AI extracts data → verification → approval → record
- **Quality Assurance** — AI runs tests → QA review → approval → release

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/unit/ -v --tb=short

# With coverage
pytest tests/unit/ -v --cov=app --cov-report=xml

# Frontend build test
cd frontend
npm run build

# Environment validation
python scripts/validate_env.py
```

## 🤖 MCP Server

Connect any MCP-compatible agent to FleetOps governance:

```bash
cd mcp-server
pip install -e .

# Run the MCP server
python fleetops-mcp.py
```

**Available MCP Tools:**
- `request_approval` — Submit actions for human approval
- `approve_request` — Approve pending requests
- `reject_request` — Reject with feedback
- `get_cost_status` — Check budget usage
- `check_danger` — Score action risk level
- `track_usage` — Log LLM API usage
- `get_hierarchy` — View agent hierarchy
- `escalate_request` — Escalate to higher authority

## 🐍 Python Client

```bash
pip install fleetops-cli
```

```python
import asyncio
from fleetops_cli import FleetOpsClient

async def main():
    async with FleetOpsClient() as client:
        # Request approval for an action
        result = await client.request_approval(
            agent_id="codex-001",
            action="deploy",
            arguments={"env": "production"}
        )
        print(f"Approval status: {result['status']}")

asyncio.run(main())
```

## 💻 CLI Tool

Command-line management for FleetOps:

```bash
cd backend
pip install -r requirements.txt

# Check system status
python cli.py status

# List pending approvals
python cli.py list

# Approve a request
python cli.py approve REQUEST-123 --scope all

# Reject with comments
python cli.py reject REQUEST-123 -c "Needs more testing"

# View agent status
python cli.py agents

# Check costs
python cli.py costs --breakdown

# View configuration
python cli.py config
```

**CLI Features:**
- Color-coded output (red/yellow/green for danger levels)
- Interactive approval prompts
- Budget progress bars
- Agent status dashboard
- Cost breakdown tables

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 💬 Community

- [GitHub Discussions](https://github.com/LunarPerovskite/FleetOps/discussions)
- [Discord](https://discord.gg/fleetops) (coming soon)
- [Telegram](https://t.me/fleetops) (coming soon)

## 🙏 Credits

Built by **LunarPerovskite** with AI assistance. FleetOps is the result of human direction and AI-powered development working together.

---

<p align="center">
  <a href="https://github.com/LunarPerovskite">@LunarPerovskite</a> on GitHub
</p>
