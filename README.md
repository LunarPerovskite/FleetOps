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
