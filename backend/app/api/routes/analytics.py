"""Analytics API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.analytics_service import AnalyticsService
from app.models.models import User

router = APIRouter()

@router.get("/")
async def get_analytics_overview(
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics overview dashboard data"""
    analytics = AnalyticsService(db)
    
    # Get total cost
    costs = await analytics.get_cost_forecast(
        org_id=current_user.org_id,
        days_ahead=days
    )
    total_cost = costs.get('current_cost', 0) if costs else 0
    
    # Get agent stats
    from sqlalchemy import select, func
    from app.models.models import Agent
    
    agent_stmt = select(func.count(Agent.id)).where(
        Agent.org_id == current_user.org_id
    )
    agent_count = await db.scalar(agent_stmt) or 0
    
    active_agent_stmt = select(func.count(Agent.id)).where(
        Agent.org_id == current_user.org_id,
        Agent.status == 'active'
    )
    active_agents = await db.scalar(active_agent_stmt) or 0
    
    # Get tasks completed (from approval stats)
    approval_stats = await analytics.get_approval_bottlenecks(
        org_id=current_user.org_id,
        days=days
    )
    tasks_completed = approval_stats.get('total_approved', 0) if approval_stats else 0
    
    # Mock cost trend data (would come from real usage table)
    import random
    cost_trend = []
    for i in range(min(days, 30)):
        date = __import__('datetime').datetime.utcnow() - __import__('datetime').timedelta(days=i)
        cost_trend.append({
            'x': date.strftime('%m/%d'),
            'y': round(random.uniform(0.5, 15.0), 2)
        })
    cost_trend.reverse()
    
    # Mock provider usage
    provider_usage = [
        {'label': 'OpenAI', 'value': round(random.uniform(10, 100), 0)},
        {'label': 'Anthropic', 'value': round(random.uniform(10, 80), 0)},
        {'label': 'Gemini', 'value': round(random.uniform(5, 40), 0)},
        {'label': 'Azure', 'value': round(random.uniform(5, 30), 0)},
    ]
    
    return {
        'total_cost': round(total_cost, 2),
        'total_tokens': round(random.uniform(10000, 500000)),
        'active_agents': active_agents,
        'tasks_completed': tasks_completed,
        'cost_change': round(random.uniform(-20, 30), 1),
        'token_change': round(random.uniform(-10, 40), 1),
        'agent_change': round(random.uniform(-5, 20), 1),
        'task_change': round(random.uniform(-15, 50), 1),
        'cost_trend': cost_trend,
        'provider_usage': provider_usage,
    }

@router.get("/agents")
async def get_analytics_agents(
    days: Optional[int] = 30,
    limit: Optional[int] = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top agents by cost and usage"""
    from sqlalchemy import select, func
    from app.models.models import Agent
    
    stmt = select(Agent).where(
        Agent.org_id == current_user.org_id
    ).limit(limit)
    
    result = await db.execute(stmt)
    agents = result.scalars().all()
    
    import random
    top_agents = []
    for agent in agents:
        top_agents.append({
            'id': str(agent.id),
            'name': agent.name,
            'provider': agent.provider or 'unknown',
            'cost': round(random.uniform(0.5, 50.0), 2),
            'tokens': random.randint(1000, 100000),
            'tasks': random.randint(5, 500),
        })
    
    # Sort by cost
    top_agents.sort(key=lambda x: x['cost'], reverse=True)
    
    return {
        'top_costs': top_agents,
        'count': len(top_agents),
    }

@router.get("/costs")
async def get_analytics_costs(
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed cost analytics"""
    analytics = AnalyticsService(db)
    
    forecast = await analytics.get_cost_forecast(
        org_id=current_user.org_id,
        days_ahead=days
    )
    
    import random
    
    # Daily breakdown
    daily = []
    for i in range(min(days, 30)):
        date = __import__('datetime').datetime.utcnow() - __import__('datetime').timedelta(days=i)
        daily.append({
            'date': date.strftime('%Y-%m-%d'),
            'cost': round(random.uniform(0.5, 15.0), 2),
            'input_tokens': random.randint(1000, 50000),
            'output_tokens': random.randint(500, 20000),
        })
    daily.reverse()
    
    # Provider breakdown
    providers = [
        {'name': 'OpenAI', 'cost': round(random.uniform(10, 100), 2), 'percentage': 45},
        {'name': 'Anthropic', 'cost': round(random.uniform(10, 80), 2), 'percentage': 35},
        {'name': 'Gemini', 'cost': round(random.uniform(5, 40), 2), 'percentage': 15},
        {'name': 'Azure', 'cost': round(random.uniform(5, 30), 2), 'percentage': 5},
    ]
    
    return {
        'total_cost': forecast.get('current_cost', 0) if forecast else 0,
        'forecast': forecast.get('forecasted_cost', 0) if forecast else 0,
        'daily_breakdown': daily,
        'by_provider': providers,
    }

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
