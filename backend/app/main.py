from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db, get_db, async_engine
from app.core.logging_config import setup_logging

# ─── Setup Logging ─────────────────────────────────────────────────────
setup_logging(level=settings.LOG_LEVEL, json_format=not settings.DEBUG)

from app.api.routes import (
    auth, organizations, teams, users, agents, tasks, approvals, 
    events, dashboard, customer_service, hierarchy, providers, 
    audit, dashboard_builder as db_builder, billing, webhooks, 
    agent_execution, agent_instances, multi_agent, llm_providers,
    openwebui, pricing, search, websocket, health, shared_agents,
    analytics, models
)

from app.core.security_middleware import SecurityMiddleware

security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    async_engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    description="The Operating System for Governed Human-Agent Work",
    version="0.1.0",
    lifespan=lifespan
)

# ─── Security Middleware ───────────────────────────────────────────────
app.add_middleware(SecurityMiddleware)

# ─── CORS ────────────────────────────────────────────────────────────
CORS_ORIGINS = (
    ["*"]
    if settings.DEBUG
    else [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        os.getenv("FRONTEND_URL", ""),
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in CORS_ORIGINS if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Root-level WebSocket for frontend ─────────────────────────────────
@app.websocket("/ws")
async def root_websocket(websocket: WebSocket):
    """Generic WebSocket for frontend connections"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
            else:
                await websocket.send_json({"type": "ack", "received": data})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(organizations.router, prefix="/api/v1/orgs", tags=["organizations"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(customer_service.router, prefix="/api/v1/customer-service", tags=["customer-service"])
app.include_router(hierarchy.router, prefix="/api/v1/hierarchy", tags=["hierarchy"])
app.include_router(providers.router, prefix="/api/v1", tags=["providers"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
app.include_router(db_builder.router, prefix="/api/v1", tags=["dashboard-builder"])
app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(agent_execution.router, prefix="/api/v1", tags=["agent-execution"])
app.include_router(agent_instances.router, prefix="/api/v1", tags=["agent-instances"])
app.include_router(multi_agent.router, prefix="/api/v1", tags=["multi-agent"])

# ─── NEW: LLM Providers & External Services ───────────────────────────
app.include_router(llm_providers.router, prefix="/api/v1", tags=["llm-providers"])
app.include_router(openwebui.router, prefix="/api/v1", tags=["openwebui"])
app.include_router(pricing.router, prefix="/api/v1", tags=["pricing"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

app.include_router(shared_agents.router, prefix="/api/v1", tags=["shared-agents"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "description": "The Operating System for Governed Human-Agent Work"
    }
