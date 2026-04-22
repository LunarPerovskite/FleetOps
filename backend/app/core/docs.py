"""API Documentation Generator for FleetOps

Auto-generates OpenAPI docs from FastAPI endpoints
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.main import app

def generate_openapi_schema():
    """Generate OpenAPI schema for documentation"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FleetOps API",
        version="0.1.0",
        description="""
        The Operating System for Governed Human-Agent Work.
        
        ## Features
        
        - **Multi-tenant** organizations with teams
        - **Human hierarchy** (Executive → Director → Senior → Operator → Reviewer → Viewer)
        - **Agent hierarchy** (Lead → Senior → Junior → Specialist → Monitor)
        - **Unlimited sub-agents** per parent agent
        - **Human-in-the-loop** at any workflow stage
        - **Immutable evidence** with cryptographic signatures
        - **Multi-channel** customer service (WhatsApp, Telegram, Web, Voice, Email, Discord)
        - **Provider agnostic** — choose your own stack
        
        ## Authentication
        
        All endpoints require a Bearer token in the Authorization header:
        ```
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        ```
        
        ## Rate Limiting
        
        API requests are rate-limited to 100 requests per minute per client.
        Check `X-RateLimit-Remaining` header for current quota.
        
        ## WebSocket
        
        Connect to `/ws` for real-time updates. Authentication via query parameter:
        ```
        ws://api.fleetops.io/ws?token=YOUR_TOKEN
        ```
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login or /auth/register"
        }
    }
    
    # Add tags
    openapi_schema["tags"] = [
        {"name": "Auth", "description": "Authentication and user management"},
        {"name": "Tasks", "description": "Task lifecycle management"},
        {"name": "Agents", "description": "Agent management and hierarchy"},
        {"name": "Approvals", "description": "Approval workflows"},
        {"name": "Events", "description": "Event logging and evidence"},
        {"name": "Dashboard", "description": "Dashboard statistics"},
        {"name": "Analytics", "description": "Performance analytics"},
        {"name": "Search", "description": "Full-text search"},
        {"name": "Customer Service", "description": "Customer service management"},
        {"name": "Hierarchy", "description": "Hierarchy configuration"},
        {"name": "Providers", "description": "Provider configuration"},
        {"name": "Onboarding", "description": "Onboarding progress"},
        {"name": "Health", "description": "Health checks"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Export schema generation
app.openapi = generate_openapi_schema
