"""Customer Service API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.customer_service import CustomerServiceManager
from app.models.models import User

router = APIRouter()

@router.post("/route")
async def route_conversation(
    conversation_id: str,
    customer_id: str,
    channel: str,
    message: str,
    sentiment_score: Optional[float] = 0.5,
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Route a customer conversation to the best agent"""
    manager = CustomerServiceManager(db)
    result = await manager.route_conversation(
        conversation_id=conversation_id,
        customer_id=customer_id,
        org_id=org_id or current_user.org_id,
        channel=channel,
        message=message,
        sentiment_score=sentiment_score
    )
    return result

@router.get("/queue/stats")
async def get_queue_stats(
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer service queue statistics"""
    manager = CustomerServiceManager(db)
    stats = await manager.get_queue_stats(
        org_id=org_id or current_user.org_id
    )
    return stats

@router.get("/sla/breaches")
async def get_sla_breaches(
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active SLA breaches"""
    manager = CustomerServiceManager(db)
    breaches = await manager.check_sla_breaches(
        org_id=org_id or current_user.org_id
    )
    return {"breaches": breaches, "count": len(breaches)}

@router.get("/{conversation_id}/handoff")
async def get_handoff_notes(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get handoff notes for human escalation"""
    manager = CustomerServiceManager(db)
    notes = await manager.generate_handoff_notes(conversation_id)
    return notes

@router.get("/customer/{customer_id}/profile")
async def get_customer_profile(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer profile with interaction history"""
    manager = CustomerServiceManager(db)
    profile = await manager.get_or_create_profile(
        customer_id=customer_id,
        org_id=current_user.org_id
    )
    return {
        "customer_id": profile.customer_id,
        "channels": profile.channels,
        "total_conversations": profile.total_conversations,
        "is_vip": profile.vip,
        "tags": profile.tags,
        "sentiment_trend": profile.sentiment_history[-5:] if profile.sentiment_history else [],
        "last_interaction": profile.last_interaction.isoformat() if profile.last_interaction else None
    }
