# FleetOps Architecture

## Overview

FleetOps is a full-stack application with a clear separation of concerns:

- **Frontend**: React SPA with real-time updates via WebSocket
- **Backend**: FastAPI with async support
- **Database**: PostgreSQL for persistence
- **Cache**: Redis for sessions, rate limiting, real-time
- **Message Queue**: Redis Pub/Sub for WebSocket broadcasts

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │Dashboard│ │  Tasks  │ │ Agents  │ │ Approvals   │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Events  │ │Customer │ │Hierarchy│ │   Audit     │  │
│  │         │ │ Service │ │         │ │    Log      │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │Settings │ │Billing  │ │  Admin  │ │ API Keys    │  │
│  │         │ │         │ │         │ │             │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                  Nginx (Reverse Proxy)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 FastAPI Backend                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │  Auth   │ │  Tasks  │ │ Agents  │ │ Approvals   │  │
│  │ Router  │ │ Router  │ │ Router  │ │  Router     │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Events  │ │Customer │ │Hierarchy│ │   Webhook   │  │
│  │ Router  │ │ Service │ │ Router  │ │   Router    │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Billing │ │  Audit  │ │Dashboard│ │  Provider   │  │
│  │ Router  │ │  Router │ │ Builder │ │   Router    │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
┌────────▼──┐ ┌───────▼────┐ ┌──────▼──────┐
│PostgreSQL │ │   Redis    │ │   Slack     │
│  (Data)   │ │  (Cache)   │ │   Discord   │
└───────────┘ └────────────┘ └─────────────┘
```

## Frontend Architecture

### Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Sidebar.tsx     # Navigation sidebar
│   │   ├── Layout.tsx      # Page layout wrapper
│   │   ├── Loading.tsx     # Loading states, skeletons
│   │   ├── ErrorDisplay.tsx # Error UI with retry
│   │   ├── StatCard.tsx    # Dashboard stat cards
│   │   ├── SearchBar.tsx   # Search with filters
│   │   ├── MobileNav.tsx   # Mobile navigation
│   │   └── EmptyState.tsx  # Empty state illustration
│   │
│   ├── pages/              # Page components (17 total)
│   │   ├── Dashboard.tsx   # Real-time dashboard
│   │   ├── Tasks.tsx       # Task management
│   │   ├── Agents.tsx      # Agent configuration
│   │   ├── Approvals.tsx   # Approval workflow
│   │   ├── Events.tsx      # Event history
│   │   ├── CustomerService.tsx # Multi-channel support
│   │   ├── Hierarchy.tsx   # Visual hierarchy builder
│   │   ├── AuditLog.tsx    # Audit trail viewer
│   │   ├── Onboarding.tsx  # 7-step setup wizard
│   │   ├── ProviderConfig.tsx # Stack selection
│   │   ├── DashboardBuilder.tsx # Custom dashboards
│   │   ├── Settings.tsx     # App settings
│   │   ├── Login.tsx       # Authentication
│   │   ├── Webhooks.tsx    # Webhook management
│   │   ├── Billing.tsx     # Usage & cost tracking
│   │   ├── Admin.tsx       # System administration
│   │   └── APIKeys.tsx     # API key management
│   │
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.tsx     # Authentication state
│   │   ├── useTheme.tsx    # Dark/light mode
│   │   ├── useWebSocket.ts # Real-time connection
│   │   ├── useWebSocketContext.tsx # WS provider
│   │   ├── useDashboard.ts # Dashboard data fetching
│   │   ├── useI18n.ts      # Internationalization
│   │   ├── useToast.ts     # Toast notifications
│   │   └── useForm.ts      # Form validation
│   │
│   ├── lib/                # Utilities
│   │   └── api.ts          # API client (all endpoints)
│   │
│   └── App.tsx             # Route configuration
```

### State Management

- **Local State**: React `useState` for component-level state
- **Global State**: Context API for auth, theme, WebSocket
- **Server State**: Direct API calls with loading/error states
- **Real-time**: WebSocket context for live updates

### Data Flow

```
User Action → API Call → Backend → Database → Response → UI Update
                                    ↓
                              WebSocket Broadcast
                                    ↓
                           Other Clients Updated
```

## Backend Architecture

### Structure

```
backend/
├── app/
│   ├── main.py             # FastAPI app, route registration
│   ├── core/               # Core utilities
│   │   ├── config.py       # Settings management
│   │   ├── database.py     # DB connection & sessions
│   │   ├── auth.py         # JWT, password hashing
│   │   ├── security.py     # CSP, XSS, CSRF headers
│   │   ├── rate_limit.py   # Rate limiting
│   │   ├── logging.py      # Structured logging
│   │   ├── error_handlers.py # Global error handling
│   │   └── docs.py         # OpenAPI documentation
│   │
│   ├── api/                # API layer
│   │   └── routes/         # 24 route modules
│   │       ├── auth.py
│   │       ├── tasks.py
│   │       ├── agents.py
│   │       ├── approvals.py
│   │       ├── events.py
│   │       ├── dashboard.py
│   │       ├── customer_service.py
│   │       ├── hierarchy.py
│   │       ├── providers.py
│   │       ├── audit.py
│   │       ├── dashboard_builder.py
│   │       ├── billing.py
│   │       ├── webhooks.py
│   │       └── ... (10 more)
│   │
│   ├── models/             # Database models
│   │   └── models.py       # SQLAlchemy models
│   │
│   ├── services/           # Business logic (17 services)
│   │   ├── task_service.py
│   │   ├── agent_service.py
│   │   ├── approval_service.py
│   │   ├── analytics_service.py
│   │   ├── billing_service.py
│   │   ├── customer_service.py
│   │   ├── search_service.py
│   │   ├── webhook_event_system.py
│   │   ├── notification_service.py
│   │   ├── auto_routing_service.py
│   │   ├── voice_service.py
│   │   ├── feature_flags.py
│   │   └── feedback_service.py
│   │
│   └── adapters/           # External integrations (11)
│       ├── auth0_adapter.py
│       ├── auth_adapter.py
│       ├── db_adapter.py
│       ├── email_adapter.py
│       ├── monitoring_adapter.py
│       ├── slack_bot_adapter.py
│       ├── discord_bot_adapter.py
│       └── cdn_adapter.py
│
├── tests/                  # Test suites (6)
├── alembic/                # Database migrations
├── scripts/                # Utility scripts
│   ├── seed_demo.py
│   └── validate_env.py
└── requirements.txt
```

### Request Lifecycle

```
Request → CORS Middleware → Rate Limit → Auth Middleware → Route Handler
                                                              ↓
                                                    Service Layer
                                                              ↓
                                                    Database Operation
                                                              ↓
                                                    Response
                                                              ↓
                                                    WebSocket Broadcast (if needed)
```

## Database Schema

### Core Tables

```sql
-- Organizations
CREATE TABLE organizations (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    tier VARCHAR DEFAULT 'free',
    created_at TIMESTAMP
);

-- Users
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    password_hash VARCHAR,
    role VARCHAR DEFAULT 'operator',
    org_id VARCHAR REFERENCES organizations(id),
    created_at TIMESTAMP
);

-- Teams
CREATE TABLE teams (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    org_id VARCHAR REFERENCES organizations(id)
);

-- Agents
CREATE TABLE agents (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    provider VARCHAR,
    model VARCHAR,
    level VARCHAR DEFAULT 'junior',
    capabilities JSON,
    status VARCHAR DEFAULT 'active',
    org_id VARCHAR REFERENCES organizations(id),
    parent_id VARCHAR REFERENCES agents(id)
);

-- Tasks
CREATE TABLE tasks (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'created',
    risk_level VARCHAR DEFAULT 'low',
    priority INTEGER DEFAULT 50,
    stage VARCHAR DEFAULT 'planning',
    agent_id VARCHAR REFERENCES agents(id),
    org_id VARCHAR REFERENCES organizations(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Approvals
CREATE TABLE approvals (
    id VARCHAR PRIMARY KEY,
    task_id VARCHAR REFERENCES tasks(id),
    human_id VARCHAR REFERENCES users(id),
    stage VARCHAR NOT NULL,
    decision VARCHAR DEFAULT 'pending',
    comments TEXT,
    created_at TIMESTAMP
);

-- Events (Audit Log)
CREATE TABLE events (
    id VARCHAR PRIMARY KEY,
    task_id VARCHAR REFERENCES tasks(id),
    event_type VARCHAR NOT NULL,
    user_id VARCHAR REFERENCES users(id),
    agent_id VARCHAR REFERENCES agents(id),
    timestamp TIMESTAMP,
    details JSON,
    signature TEXT,
    signature_verified BOOLEAN DEFAULT FALSE
);

-- Webhooks
CREATE TABLE webhooks (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR REFERENCES organizations(id),
    url VARCHAR NOT NULL,
    events VARCHAR,
    secret VARCHAR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);
```

## Provider Architecture

FleetOps is designed to be provider-agnostic through adapter pattern:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FleetOps  │────▶│  Adapter    │────▶│  Provider   │
│   Core      │     │  Interface  │     │  (Clerk,    │
│             │     │             │     │  Auth0,     │
│             │     │  authenticate() │  │  Okta...)   │
│             │     │  get_user()     │  │             │
│             │     │  validate()     │  │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

This allows users to:
- Swap auth providers without code changes
- Choose their preferred database
- Use existing infrastructure
- Avoid vendor lock-in

## Real-Time Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │◄───▶│  WebSocket   │◄───▶│  Server  │
│  Browser │     │  Connection  │     │  Events  │
└──────────┘     └──────────────┘     └──────────┘
                                              │
                                              ▼
                                       ┌──────────┐
                                       │  Redis   │
                                       │  Pub/Sub │
                                       └──────────┘
                                              │
                                              ▼
                                       ┌──────────┐
                                       │  Other   │
                                       │  Clients │
                                       └──────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────┐
│              Security Layers              │
├─────────────────────────────────────────┤
│ 1. HTTPS (TLS 1.3)                      │
│ 2. CORS Configuration                   │
│ 3. Rate Limiting (Redis-backed)         │
│ 4. JWT Authentication                   │
│ 5. Role-Based Access Control            │
│ 6. Input Validation (Pydantic)          │
│ 7. Output Sanitization                  │
│ 8. CSP Headers                          │
│ 9. XSS Protection                       │
│ 10. CSRF Protection                     │
│ 11. HSTS Headers                        │
│ 12. SQL Injection Prevention            │
│ 13. PBKDF2 Password Hashing           │
│ 14. Immutable Evidence Store            │
│ 15. Audit Logging                       │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Docker (Development)

```
┌─────────────────────────────────────────┐
│           Docker Compose                │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │Frontend │ │ Backend │ │ Postgres │ │
│  │ :3000   │ │ :8000   │ │  :5432   │ │
│  └─────────┘ └─────────┘ └──────────┘ │
│  ┌─────────┐ ┌─────────┐              │
│  │  Redis  │ │  Nginx  │              │
│  │ :6379   │ │ :80     │              │
│  └─────────┘ └─────────┘              │
└─────────────────────────────────────────┘
```

### Kubernetes (Production)

```
┌─────────────────────────────────────────┐
│           Kubernetes Cluster            │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │Frontend │ │ Backend │ │ Postgres │ │
│  │  Pods   │ │  Pods   │ │  Stateful│ │
│  │  (3)    │ │  (3)    │ │  Set     │ │
│  └─────────┘ └─────────┘ └──────────┘ │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │  Redis  │ │  Nginx  │ │  Backup  │ │
│  │  Pods   │ │Ingress  │ │  CronJob │ │
│  │  (3)    │ │Controller│ │          │ │
│  └─────────┘ └─────────┘ └──────────┘ │
└─────────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

- **Stateless Backend**: Any instance can handle any request
- **Redis Session Store**: Shared state across instances
- **Database**: Read replicas for analytics queries
- **WebSocket**: Redis Pub/Sub for cross-instance broadcast

### Caching Strategy

| Layer | Cache | TTL | Invalidation |
|-------|-------|-----|--------------|
| API Response | Redis | 5 min | On write |
| Dashboard Stats | Redis | 1 min | WebSocket event |
| User Session | Redis | 24h | Logout |
| Agent Config | Memory | ∞ | Restart |

## Development Guidelines

### Adding a New Feature

1. **Backend**: Create route in `app/api/routes/`
2. **Service**: Add business logic in `app/services/`
3. **Frontend**: Create page in `frontend/src/pages/`
4. **API Client**: Add endpoint in `frontend/src/lib/api.ts`
5. **Navigation**: Add to `frontend/src/components/Sidebar.tsx`
6. **Tests**: Add tests in `backend/tests/`

### Code Organization Principles

- **Single Responsibility**: One service per domain
- **Dependency Injection**: Pass dependencies, don't hardcode
- **Adapter Pattern**: Abstract external services
- **Event-Driven**: Use events for cross-cutting concerns
- **Immutable Records**: Never modify audit events

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time | < 200ms (p95) |
| Page Load | < 2s |
| WebSocket Latency | < 50ms |
| Database Query | < 100ms |
| Concurrent Users | 10,000+ |

---

*Last updated: 2026-04-22*
