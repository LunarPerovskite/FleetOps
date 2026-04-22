"""Advanced Analytics for FleetOps

Features:
- Agent performance scoring (speed, quality, cost-efficiency)
- Task completion metrics
- Cost analysis and forecasting
- Time-to-completion tracking
- Approval bottleneck detection
- Customer satisfaction trends
- Predictive alerting
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.models import (
    Agent, Task, Event, Approval, LLMUsage, User,
    TaskStatus, RiskLevel
)

class AnalyticsService:
    """Advanced analytics and performance scoring"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_agent_performance(self, agent_id: str, 
                                    days: int = 30) -> Dict:
        """Calculate comprehensive agent performance score"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Task metrics
        tasks_result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.agent_id == agent_id,
                    Task.created_at >= since
                )
            )
        )
        tasks = tasks_result.scalars().all()
        
        total_tasks = len(tasks)
        if total_tasks == 0:
            return {"error": "No tasks found for this period"}
        
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        cancelled = [t for t in tasks if t.status == TaskStatus.CANCELLED]
        
        completion_rate = len(completed) / total_tasks * 100
        failure_rate = len(failed) / total_tasks * 100
        
        # Time metrics
        completion_times = []
        for task in completed:
            if task.completed_at and task.created_at:
                duration = (task.completed_at - task.created_at).total_seconds() / 60
                completion_times.append(duration)
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Cost metrics
        cost_result = await self.db.execute(
            select(func.sum(LLMUsage.cost)).where(
                and_(
                    LLMUsage.agent_id == agent_id,
                    LLMUsage.timestamp >= since
                )
            )
        )
        total_cost = cost_result.scalar() or 0
        avg_cost_per_task = total_cost / total_tasks
        
        # Approval metrics
        approval_result = await self.db.execute(
            select(Approval).where(
                and_(
                    Approval.task_id.in_([t.id for t in tasks]),
                    Approval.decision == "approve"
                )
            )
        )
        approvals = approval_result.scalars().all()
        
        approval_times = []
        for approval in approvals:
            if approval.resolved_at and approval.created_at:
                duration = (approval.resolved_at - approval.created_at).total_seconds() / 60
                approval_times.append(duration)
        
        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
        
        # Performance score (0-100)
        # Completion rate: 40%, Speed: 20%, Cost efficiency: 20%, Approval time: 20%
        speed_score = max(0, 100 - (avg_completion_time / 10))  # Lower is better
        cost_score = max(0, 100 - (avg_cost_per_task * 100))  # Lower cost is better
        approval_score = max(0, 100 - (avg_approval_time / 5))  # Faster approval is better
        
        overall_score = (
            completion_rate * 0.4 +
            speed_score * 0.2 +
            cost_score * 0.2 +
            approval_score * 0.2
        )
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "overall_score": round(overall_score, 2),
            "breakdown": {
                "completion_rate": round(completion_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "speed_score": round(speed_score, 2),
                "cost_score": round(cost_score, 2),
                "approval_score": round(approval_score, 2)
            },
            "metrics": {
                "total_tasks": total_tasks,
                "completed": len(completed),
                "failed": len(failed),
                "cancelled": len(cancelled),
                "avg_completion_time_minutes": round(avg_completion_time, 2),
                "avg_cost_per_task": round(avg_cost_per_task, 4),
                "total_cost": round(total_cost, 4),
                "avg_approval_time_minutes": round(avg_approval_time, 2)
            },
            "grade": self._calculate_grade(overall_score)
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90: return "A+"
        if score >= 85: return "A"
        if score >= 80: return "A-"
        if score >= 75: return "B+"
        if score >= 70: return "B"
        if score >= 65: return "B-"
        if score >= 60: return "C+"
        if score >= 55: return "C"
        if score >= 50: return "C-"
        return "D"
    
    async def get_team_performance(self, team_id: str, 
                                   days: int = 30) -> Dict:
        """Get aggregate performance for a team"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get all agents in team
        agents_result = await self.db.execute(
            select(Agent).where(Agent.team_id == team_id)
        )
        agents = agents_result.scalars().all()
        
        agent_scores = []
        for agent in agents:
            perf = await self.get_agent_performance(agent.id, days)
            if "error" not in perf:
                agent_scores.append(perf)
        
        if not agent_scores:
            return {"error": "No performance data available"}
        
        # Aggregate metrics
        avg_score = sum(a["overall_score"] for a in agent_scores) / len(agent_scores)
        total_tasks = sum(a["metrics"]["total_tasks"] for a in agent_scores)
        total_cost = sum(a["metrics"]["total_cost"] for a in agent_scores)
        
        return {
            "team_id": team_id,
            "period_days": days,
            "agent_count": len(agents),
            "avg_team_score": round(avg_score, 2),
            "total_tasks": total_tasks,
            "total_cost": round(total_cost, 4),
            "top_performer": max(agent_scores, key=lambda x: x["overall_score"]),
            "bottom_performer": min(agent_scores, key=lambda x: x["overall_score"]),
            "agent_breakdown": agent_scores
        }
    
    async def get_cost_forecast(self, org_id: str, 
                                days_ahead: int = 30) -> Dict:
        """Predict future costs based on historical trends"""
        # Get last 90 days of data
        since = datetime.utcnow() - timedelta(days=90)
        
        daily_costs = await self.db.execute(
            select(
                func.date(LLMUsage.timestamp).label('date'),
                func.sum(LLMUsage.cost).label('daily_cost'),
                func.sum(LLMUsage.tokens_in + LLMUsage.tokens_out).label('daily_tokens')
            ).where(
                and_(
                    LLMUsage.org_id == org_id,
                    LLMUsage.timestamp >= since
                )
            ).group_by(
                func.date(LLMUsage.timestamp)
            ).order_by(
                func.date(LLMUsage.timestamp)
            )
        )
        
        daily_data = daily_costs.all()
        
        if not daily_data:
            return {"error": "No historical data for forecasting"}
        
        # Simple linear trend
        costs = [row.daily_cost for row in daily_data]
        avg_daily = sum(costs) / len(costs)
        trend = (costs[-1] - costs[0]) / len(costs) if len(costs) > 1 else 0
        
        forecast = []
        for i in range(1, days_ahead + 1):
            predicted = avg_daily + (trend * i)
            forecast.append({
                "day": i,
                "predicted_cost": round(max(0, predicted), 4),
                "confidence": max(0, 100 - i * 2)  # Confidence decreases over time
            })
        
        total_predicted = sum(f["predicted_cost"] for f in forecast)
        
        return {
            "org_id": org_id,
            "days_ahead": days_ahead,
            "historical_avg_daily": round(avg_daily, 4),
            "trend": round(trend, 4),
            "total_predicted": round(total_predicted, 4),
            "forecast": forecast
        }
    
    async def get_approval_bottlenecks(self, org_id: str,
                                       days: int = 7) -> Dict:
        """Identify approval bottlenecks in the organization"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get pending approvals by stage
        pending_by_stage = await self.db.execute(
            select(
                Approval.stage,
                func.count(Approval.id).label('count'),
                func.avg(
                    func.extract('epoch', datetime.utcnow() - Approval.created_at) / 60
                ).label('avg_wait_minutes')
            ).where(
                and_(
                    Approval.decision.is_(None),
                    Approval.created_at >= since
                )
            ).group_by(
                Approval.stage
            )
        )
        
        stage_data = pending_by_stage.all()
        
        # Get pending by approver
        pending_by_approver = await self.db.execute(
            select(
                User.name,
                User.role,
                func.count(Approval.id).label('count'),
                func.max(
                    func.extract('epoch', datetime.utcnow() - Approval.created_at) / 60
                ).label('max_wait_minutes')
            ).join(
                Approval, Approval.human_id == User.id
            ).where(
                and_(
                    Approval.decision.is_(None),
                    Approval.created_at >= since
                )
            ).group_by(
                User.id
            )
        )
        
        approver_data = pending_by_approver.all()
        
        return {
            "period_days": days,
            "total_pending": sum(s.count for s in stage_data),
            "by_stage": [
                {
                    "stage": s.stage,
                    "count": s.count,
                    "avg_wait_minutes": round(s.avg_wait_minutes or 0, 2)
                }
                for s in stage_data
            ],
            "by_approver": [
                {
                    "name": a.name,
                    "role": a.role,
                    "pending_count": a.count,
                    "max_wait_minutes": round(a.max_wait_minutes or 0, 2)
                }
                for a in approver_data
            ],
            "bottlenecks": [
                {
                    "type": "stage",
                    "id": s.stage,
                    "severity": "high" if s.count > 10 else "medium" if s.count > 5 else "low"
                }
                for s in stage_data if s.count > 5
            ]
        }
    
    async def get_customer_satisfaction_trends(self, org_id: str,
                                                days: int = 30) -> Dict:
        """Track customer satisfaction over time"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get sentiment data from events
        sentiment_events = await self.db.execute(
            select(Event).where(
                and_(
                    Event.event_type == "sentiment_analysis",
                    Event.data.contains({"org_id": org_id}),
                    Event.timestamp >= since
                )
            ).order_by(Event.timestamp)
        )
        
        events = sentiment_events.scalars().all()
        
        if not events:
            return {"error": "No sentiment data available"}
        
        # Calculate daily averages
        daily_sentiments = {}
        for event in events:
            day = event.timestamp.date().isoformat()
            score = event.data.get("sentiment_score", 0.5)
            
            if day not in daily_sentiments:
                daily_sentiments[day] = []
            daily_sentiments[day].append(score)
        
        trends = []
        for day, scores in sorted(daily_sentiments.items()):
            avg = sum(scores) / len(scores)
            trends.append({
                "date": day,
                "avg_sentiment": round(avg, 3),
                "sample_size": len(scores),
                "mood": "positive" if avg > 0.6 else "neutral" if avg > 0.4 else "negative"
            })
        
        # Overall trend
        if len(trends) >= 2:
            first_week = trends[:7]
            last_week = trends[-7:]
            first_avg = sum(t["avg_sentiment"] for t in first_week) / len(first_week)
            last_avg = sum(t["avg_sentiment"] for t in last_week) / len(last_week)
            trend_direction = "improving" if last_avg > first_avg else "declining" if last_avg < first_avg else "stable"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "period_days": days,
            "trend_direction": trend_direction,
            "current_avg": round(trends[-1]["avg_sentiment"], 3) if trends else 0,
            "daily_trends": trends
        }
