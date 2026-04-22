"""Analytics API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.analytics_service import AnalyticsService
from app.models.models import User

router = APIRouter()

@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive agent performance score"""
    analytics = AnalyticsService(db)
    result = await analytics.get_agent_performance(agent_id, days)
    return result

@router.get("/teams/{team_id}/performance")
async def get_team_performance(
    team_id: str,
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team performance metrics"""
    analytics = AnalyticsService(db)
    result = await analytics.get_team_performance(team_id, days)
    return result

@router.get("/costs/forecast")
async def get_cost_forecast(
    days_ahead: Optional[int] = 30,
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cost forecast for organization"""
    analytics = AnalyticsService(db)
    result = await analytics.get_cost_forecast(
        org_id=org_id or current_user.org_id,
        days_ahead=days_ahead
    )
    return result

@router.get("/approvals/bottlenecks")
async def get_approval_bottlenecks(
    days: Optional[int] = 7,
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get approval bottleneck analysis"""
    analytics = AnalyticsService(db)
    result = await analytics.get_approval_bottlenecks(
        org_id=org_id or current_user.org_id,
        days=days
    )
    return result

@router.get("/sentiment/trends")
async def get_sentiment_trends(
    days: Optional[int] = 30,
    org_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer satisfaction trends"""
    analytics = AnalyticsService(db)
    result = await analytics.get_customer_satisfaction_trends(
        org_id=org_id or current_user.org_id,
        days=days
    )
    return result
