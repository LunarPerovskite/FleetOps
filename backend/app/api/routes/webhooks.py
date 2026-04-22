"""Webhook API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.webhook_service import WebhookService
from app.models.models import User

router = APIRouter()

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
