# FleetOps

> **The Operating System for Governed Human-Agent Work**

FleetOps is an open-source governance platform that connects your existing AI agents (Claude Code, Codex, Copilot, etc.) with human oversight at every stage. Organizations maintain full control while agents handle the heavy lifting.

![Status](https://img.shields.io/badge/status-beta-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18-blue)

## 🚀 What FleetOps Does

- **Human-in-the-Loop**: Insert human approval at any workflow stage
- **Agent Hierarchy**: Organize agents with customizable levels and unlimited sub-agents
- **Evidence Store**: Immutable, cryptographically signed audit trail
- **Multi-Channel Customer Service**: WhatsApp, Telegram, Web Chat, Voice, Email, Discord
- **Provider Agnostic**: Choose your own stack (Clerk, Auth0, Okta, Supabase, AWS, etc.)
- **Cross-Channel Context**: Conversations flow seamlessly between channels

## 📸 Screenshots

- Dashboard with real-time updates
- Approval workflow with SLA tracking
- Provider configuration UI
- Custom dashboard builder

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

## 🚦 Quick Start

### Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps

# Copy environment variables
cp .env.example .env
# Edit .env with your settings

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

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
```

## 🏢 Self-Hosted vs SaaS

| Feature | Self-Hosted (Free) | FleetOps Cloud |
|---------|-------------------|----------------|
| Agents | Unlimited | Unlimited |
| Teams | Unlimited | Unlimited |
| Storage | Your infrastructure | Managed |
| Support | Community | Priority |
| Price | Free | From $29/mo |

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
