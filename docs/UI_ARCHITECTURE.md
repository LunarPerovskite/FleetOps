# FleetOps UI Architecture

## Page Overview (23 pages)

### 🏠 Public Pages
| Page | Lines | Description |
|------|-------|-------------|
| **LandingPage.tsx** | 208 | Marketing page with hero, features, pricing |
| **Login.tsx** | 133 | Auth with email/password |

### 📊 Dashboard Pages
| Page | Lines | Description |
|------|-------|-------------|
| **Dashboard.tsx** | 278 | Main dashboard with stats, recent activity |
| **DashboardBuilder.tsx** | 207 | Custom dashboard widget builder |

### 🤖 Agent Management
| Page | Lines | Description |
|------|-------|-------------|
| **Agents.tsx** | 258 | Agent list, create, edit, delete |
| **AgentInstances.tsx** | 656 | Live agent monitoring, status, logs |

### 📋 Task Management
| Page | Lines | Description |
|------|-------|-------------|
| **Tasks.tsx** | 227 | Task list with status filters |
| **Approvals.tsx** | 211 | Human approval queue for critical tasks |

### 💰 Cost & Billing
| Page | Lines | Description |
|------|-------|-------------|
| **Billing.tsx** | 149 | Usage stats, cost reports |

### 🔒 Security & Compliance
| Page | Lines | Description |
|------|-------|-------------|
| **AuditLog.tsx** | 184 | Immutable audit trail viewer |
| **APIKeys.tsx** | 278 | API key management with scopes |

### 🏗️ Organization
| Page | Lines | Description |
|------|-------|-------------|
| **Hierarchy.tsx** | 202 | Org hierarchy, roles, approval ladders |
| **Admin.tsx** | 291 | System admin panel |
| **Settings.tsx** | 155 | User/org settings |

### 🔌 Integrations
| Page | Lines | Description |
|------|-------|-------------|
| **Integrations.tsx** | 419 | Provider integrations (LLM, auth, DB) |
| **ProviderConfig.tsx** | 250 | Configure adapters (Clerk, Supabase, etc) |
| **Marketplace.tsx** | 260 | Plugin marketplace |

### 📞 Customer Service
| Page | Lines | Description |
|------|-------|-------------|
| **CustomerService.tsx** | 273 | CS agent sessions, handoff |

### ⚙️ DevOps
| Page | Lines | Description |
|------|-------|-------------|
| **Events.tsx** | 163 | Event stream, webhooks |
| **Webhooks.tsx** | 210 | Webhook configuration |
| **WorkflowTemplates.tsx** | 210 | Reusable workflow templates |

### 🎯 Onboarding
| Page | Lines | Description |
|------|-------|-------------|
| **Onboarding.tsx** | 308 | Step-by-step setup wizard |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FleetOps Frontend                         │
│                    (React + TypeScript + Vite)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Landing  │  │  Login   │  │  Admin   │  │ Settings │     │
│  │   Page    │  │          │  │  Panel   │  │          │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    MAIN DASHBOARD                        │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │  Stats  │ │ Recent  │ │ Agent   │ │ Budget  │       │    │
│  │  │ Cards   │ │Activity │ │ Status  │ │ Chart   │       │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Agents  │  │  Tasks   │  │Approvals │  │ Billing  │       │
│  │ Manager  │  │ Manager  │  │  Queue   │  │  Report  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ AuditLog │  │Hierarchy │  │Integra-  │  │Provider  │       │
│  │  Viewer  │  │  Builder │  │  tions   │  │  Config  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │  Events  │  │Webhooks  │  │   CS     │                    │
│  │  Stream  │  │ Manager  │  │  Panel   │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │  HTTP/WebSocket
                   │
┌──────────────────▼───────────────────────────────────────────────┐
│                      FleetOps Backend (FastAPI)                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Auth      │  │   Tasks     │  │   Agents    │              │
│  │ (JWT/Clerk) │  │  (CRUD)     │  │  (CRUD)     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Approvals   │  │   Events    │  │   Billing   │              │
│  │  (Flow)     │  │  (Stream)   │  │  (Usage)    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  AuditLog   │  │  Hierarchy  │  │  Analytics  │              │
│  │ (Immutable) │  │  (Roles)    │  │  (Metrics)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Core Services                            │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │    │
│  │  │ Cost   │ │Circuit │ │Budget  │ │Usage   │         │    │
│  │  │Track   │ │Breaker │ │Enforce │ │Extract │         │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘         │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │    │
│  │  │Security│ │Audit   │ │Pricing │ │Config  │         │    │
│  │  │Midware │ │Logger  │ │Cache   │ │Loader  │         │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  20+ Adapters                           │    │
│  │  OpenAI  Anthropic  Gemini  Azure  Ollama  OpenWebUI   │    │
│  │  Clerk   Supabase   Vercel  AWS     GCP    Cloudflare   │    │
│  │  Redis   Sentry    Datadog  Stripe  Twilio  SendGrid    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                    │
└──────────────────┬─────────────────────────────────────────────────┘
                   │
                   │  SQL / Redis / WebSocket
                   │
┌──────────────────▼─────────────────────────────────────────────────┐
│                         Data Layer                                │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ PostgreSQL  │  │    Redis    │  │  Filesystem │              │
│  │  (Primary)  │  │  (Cache/    │  │  (Uploads)  │              │
│  │             │  │   Queue)    │  │             │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└────────────────────────────────────────────────────────────────────┘
```

## Key UI Features

### Dashboard Builder
- Drag-and-drop widget customization
- Real-time metrics (active agents, task queue, costs)
- Customizable layout with persisted state

### Agent Management
- Agent list with status badges (active/idle/error)
- Sub-agent hierarchy visualization
- Cost tracking per agent
- Live monitoring of running instances

### Task Approval Flow
- Queue of tasks pending human approval
- Risk scoring and auto-approval rules
- One-click approve/reject with comments
- Escalation to higher hierarchy levels

### Cost Tracking
- Real-time budget usage with progress bars
- Provider breakdown (OpenAI, Anthropic, etc.)
- Per-agent, per-team cost attribution
- Budget alerts and hard stops

### Integrations
- Visual provider cards (Claude, GPT, Gemini, etc.)
- One-click configuration with env var setup
- Health status indicators
- Connection testing

### Hierarchy & Organization
- Org chart with drag-and-drop roles
- Approval ladder configuration
- Team management with budget allocation
- Permission matrix visualization
