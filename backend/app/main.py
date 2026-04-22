from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, get_db, async_engine
from app.api.routes import auth, organizations, teams, users, agents, tasks, approvals, events, dashboard, customer_service, hierarchy, providers, audit, dashboard_builder as db_builder, billing, webhooks, agent_execution, agent_instances, multi_agent

security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    await async_engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    description="The Operating System for Governed Human-Agent Work",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
