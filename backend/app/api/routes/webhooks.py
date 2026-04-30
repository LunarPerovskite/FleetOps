"""Webhook API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.services.webhook_service import WebhookService
from app.services.webhook_event_system import webhook_system
from app.models.models import User

router = APIRouter()

@router.get("/webhooks")
async def list_webhooks(
    current_user: User = Depends(get_current_user)
):
    """List all webhooks for organization"""
    # In production, fetch from database
    return {"webhooks": []}

@router.post("/webhooks")
async def create_webhook(
    url: str,
    events: str,
    secret: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new webhook"""
    # In production, save to database
    return {
        "id": f"wh_{hash(url) % 10000}",
        "url": url,
        "events": events,
        "secret": bool(secret),
        "active": True
    }

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a webhook"""
    return {"message": "Webhook deleted"}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Test webhook with ping event"""
    result = await webhook_system.test_webhook(webhook_id)
    return result

@router.post("/register")
async def register_webhook(
    url: str,
    events: List[str],
    secret: str,
    headers: Optional[dict] = None,
    org_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Register a webhook for events"""
    service = WebhookService()
    result = service.register_webhook(
        org_id=org_id or current_user.org_id,
        url=url,
        events=events,
        secret=secret,
        headers=headers
    )
    return result

@router.get("/status")
async def get_webhook_status(
    org_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get webhook status"""
    service = WebhookService()
    result = service.get_webhook_status(
        org_id=org_id or current_user.org_id
    )
    return result
