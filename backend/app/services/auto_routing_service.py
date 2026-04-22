"""AI-Powered Auto-Routing Service for FleetOps

Smart task routing to best agent based on:
- Capability matching
- Current workload
- Historical performance
- Task complexity
"""

from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class AgentScore:
    agent_id: str
    agent_name: str
    score: float
    reason: str
    workload: int
    avg_latency_ms: float
    success_rate: float

class AutoRoutingService:
    """Intelligent task routing without external ML models"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def find_best_agent(
        self,
        task_type: str,
        required_capabilities: List[str],
        risk_level: str = "low",
        exclude_agents: List[str] = None
    ) -> Optional[AgentScore]:
        """Find the best agent for a task"""
        
        # Get all active agents
        from app.models.models import Agent
        
        agents = self.db.query(Agent).filter(
            Agent.status == "active"
        ).all()
        
        if not agents:
            return None
        
        scores = []
        
        for agent in agents:
            if exclude_agents and agent.id in exclude_agents:
                continue
            
            # Calculate composite score
            score = await self._calculate_agent_score(
                agent, task_type, required_capabilities, risk_level
            )
            scores.append(score)
        
        if not scores:
            return None
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x.score, reverse=True)
        
        return scores[0]
    
    async def _calculate_agent_score(
        self,
        agent,
        task_type: str,
        required_capabilities: List[str],
        risk_level: str
    ) -> AgentScore:
        """Calculate agent suitability score (0-100)"""
        
        scores = []
        reasons = []
        
        # 1. Capability Match (40% weight)
        agent_caps = agent.capabilities or []
        matched_caps = set(required_capabilities) & set(agent_caps)
        capability_score = (len(matched_caps) / len(required_capabilities)) * 40 if required_capabilities else 20
        scores.append(capability_score)
        reasons.append(f"Capability match: {len(matched_caps)}/{len(required_capabilities)}")
        
        # 2. Workload Balance (30% weight)
        current_tasks = await self._get_agent_workload(agent.id)
        max_tasks = 10  # Configurable
        workload_score = max(0, 30 - (current_tasks / max_tasks) * 30)
        scores.append(workload_score)
        reasons.append(f"Workload: {current_tasks} tasks")
        
        # 3. Historical Performance (20% weight)
        performance = await self._get_agent_performance(agent.id)
        perf_score = performance["success_rate"] * 20
        scores.append(perf_score)
        reasons.append(f"Success rate: {performance['success_rate']:.0%}")
        
        # 4. Risk Alignment (10% weight)
        risk_scores = {"low": 10, "medium": 8, "high": 5, "critical": 2}
        agent_level_scores = {"lead": 10, "senior": 8, "junior": 5, "specialist": 7, "monitor": 3}
        risk_alignment = min(
            risk_scores.get(risk_level, 5),
            agent_level_scores.get(agent.level or "junior", 5)
        )
        scores.append(risk_alignment)
        reasons.append(f"Level: {agent.level}")
        
        # Calculate total score
        total_score = sum(scores)
        
        return AgentScore(
            agent_id=agent.id,
            agent_name=agent.name,
            score=total_score,
            reason="; ".join(reasons),
            workload=current_tasks,
            avg_latency_ms=performance["avg_latency_ms"],
            success_rate=performance["success_rate"]
        )
    
    async def _get_agent_workload(self, agent_id: str) -> int:
        """Get current agent task count"""
        from app.models.models import Task
        
        return self.db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.status.in_(["created", "planning", "executing"])
        ).count()
    
    async def _get_agent_performance(self, agent_id: str) -> Dict:
        """Get agent historical performance"""
        from app.models.models import Task, Event
        from sqlalchemy import func
        
        # Get completed tasks
        completed = self.db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.status == "completed"
        ).count()
        
        failed = self.db.query(Task).filter(
            Task.agent_id == agent_id,
            Task.status == "failed"
        ).count()
        
        total = completed + failed
        
        # Calculate average latency from events
        avg_latency = self.db.query(func.avg(Event.latency_ms)).filter(
            Event.agent_id == agent_id
        ).scalar() or 0
        
        return {
            "success_rate": (completed / total) if total > 0 else 0.5,
            "avg_latency_ms": avg_latency,
            "total_tasks": total,
            "completed": completed,
            "failed": failed
        }
    
    async def predict_escalation_need(
        self,
        task_id: str
    ) -> Dict:
        """Predict if a task needs escalation"""
        from app.models.models import Task, Event
        
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"needs_escalation": False, "reason": "Task not found"}
        
        reasons = []
        escalation_probability = 0.0
        
        # Factor 1: Risk level
        if task.risk_level in ["high", "critical"]:
            escalation_probability += 0.3
            reasons.append("High risk level")
        
        # Factor 2: Multiple failures
        recent_failures = self.db.query(Event).filter(
            Event.task_id == task_id,
            Event.event_type == "agent_error"
        ).count()
        
        if recent_failures >= 3:
            escalation_probability += 0.4
            reasons.append(f"{recent_failures} recent failures")
        elif recent_failures > 0:
            escalation_probability += 0.1 * recent_failures
            reasons.append(f"{recent_failures} failure(s)")
        
        # Factor 3: Long execution time
        # Check if task has been running too long
        from datetime import timedelta
        if task.created_at and (datetime.utcnow() - task.created_at) > timedelta(hours=1):
            escalation_probability += 0.2
            reasons.append("Running over 1 hour")
        
        return {
            "needs_escalation": escalation_probability > 0.5,
            "escalation_probability": min(escalation_probability, 1.0),
            "reasons": reasons,
            "suggested_action": "escalate" if escalation_probability > 0.5 else "continue_monitoring"
        }
    
    async def get_routing_recommendations(
        self,
        org_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get top agent recommendations for the org"""
        
        from app.models.models import Agent
        
        agents = self.db.query(Agent).filter(
            Agent.org_id == org_id,
            Agent.status == "active"
        ).limit(limit).all()
        
        recommendations = []
        
        for agent in agents:
            performance = await self._get_agent_performance(agent.id)
            workload = await self._get_agent_workload(agent.id)
            
            recommendations.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "capabilities": agent.capabilities,
                "workload": workload,
                "performance": performance,
                "recommendation": "underutilized" if workload < 3 else "optimal" if workload < 8 else "overloaded"
            })
        
        return recommendations
