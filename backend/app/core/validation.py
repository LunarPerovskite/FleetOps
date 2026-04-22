"""Input Validation Schemas for FleetOps

Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

class CreateTaskRequest(BaseModel):
    """Task creation request"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    agent_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    risk_level: str = Field("low", regex="^(low|medium|high|critical|blocked)$")
    priority: int = Field(0, ge=0, le=100)
    
    @validator('risk_level')
    def validate_risk(cls, v):
        allowed = ["low", "medium", "high", "critical", "blocked"]
        if v not in allowed:
            raise ValueError(f"risk_level must be one of {allowed}")
        return v

class ApprovalRequest(BaseModel):
    """Task approval request"""
    decision: str = Field(..., regex="^(approve|reject|request_changes|escalate)$")
    comments: Optional[str] = Field(None, max_length=2000)
    human_id: str = Field(..., min_length=1)

class CreateAgentRequest(BaseModel):
    """Agent creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., min_length=1)
    model: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    level: str = Field("junior", regex="^(junior|senior|lead|specialist|monitor)$")
    org_id: Optional[str] = None
    team_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    max_sub_agents: Optional[int] = Field(None, ge=0, le=1000)

class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str = Field(..., min_length=8)

class RegisterRequest(BaseModel):
    """Registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=255)
    org_name: Optional[str] = Field(None, max_length=255)

class WebhookConfigRequest(BaseModel):
    """Webhook configuration"""
    url: str = Field(..., regex="^https?://")
    events: List[str] = Field(..., min_items=1)
    secret: str = Field(..., min_length=16)
    headers: Optional[Dict[str, str]] = None

class ProviderConfigRequest(BaseModel):
    """Provider configuration"""
    auth_provider: str = Field(..., regex="^(clerk|auth0|okta|azure_ad|cognito|self_hosted)$")
    database: str = Field(..., regex="^(supabase|neon|aws_rds|postgres|sqlite)$")
    hosting: str = Field(..., regex="^(vercel|railway|render|aws|gcp|azure|self_hosted)$")
    secrets: str = Field(..., regex="^(doppler|vault|aws_secrets|azure_keyvault|env)$")
    monitoring: str = Field("sentry", regex="^(datadog|sentry|cloudwatch|grafana|none)$")
    cdn: str = Field("cloudflare", regex="^(cloudflare|aws_cloudfront|vercel_edge|none)$")

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class SearchFilterRequest(BaseModel):
    """Search filter parameters"""
    search_text: Optional[str] = Field(None, max_length=200)
    status: Optional[List[str]] = None
    priority: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    agent_id: Optional[str] = None
    org_id: Optional[str] = None

class ConfigResponse(BaseModel):
    """Configuration response"""
    success: bool
    message: str
    data: Optional[Dict] = None
    errors: Optional[List[str]] = None
