"""Billing Service for FleetOps

Handles subscriptions, invoices, usage tracking.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import LLMUsage, Organization, User

class BillingService:
    """Billing and subscription management"""
    
    TIERS = {
        "free": {
            "price": 0,
            "agents": 3,
            "teams": 1,
            "logs_gb": 1,
            "support": "community"
        },
        "pro": {
            "price": 29,
            "agents": float('inf'),
            "teams": float('inf'),
            "logs_gb": 50,
            "support": "email"
        },
        "business": {
            "price": 99,
            "agents": float('inf'),
            "teams": float('inf'),
            "logs_gb": 200,
            "support": "priority",
            "features": ["sso", "analytics", "compliance_exports", "api_access"]
        },
        "enterprise": {
            "price": "custom",
            "agents": float('inf'),
            "teams": float('inf'),
            "logs_gb": float('inf'),
            "support": "dedicated",
            "features": ["self_hosted", "sla", "custom_contract"]
        }
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_usage_this_month(self, org_id: str) -> Dict:
        """Get current month's usage"""
        now = datetime.utcnow()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # LLM costs
        llm_cost = await self.db.execute(
            select(func.sum(LLMUsage.cost)).where(
                LLMUsage.org_id == org_id,
                LLMUsage.timestamp >= first_day
            )
        )
        
        # Token usage
        tokens = await self.db.execute(
            select(func.sum(LLMUsage.tokens_in + LLMUsage.tokens_out)).where(
                LLMUsage.org_id == org_id,
                LLMUsage.timestamp >= first_day
            )
        )
        
        # Number of agents
        from app.models.models import Agent
        agent_count = await self.db.execute(
            select(func.count(Agent.id)).where(
                Agent.org_id == org_id,
                Agent.status == "active"
            )
        )
        
        # Number of tasks
        from app.models.models import Task
        task_count = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.org_id == org_id,
                Task.created_at >= first_day
            )
        )
        
        return {
            "month": now.strftime("%Y-%m"),
            "llm_cost": llm_cost.scalar() or 0.0,
            "total_tokens": tokens.scalar() or 0,
            "active_agents": agent_count.scalar() or 0,
            "tasks_created": task_count.scalar() or 0,
            "billing_period_start": first_day.isoformat(),
            "billing_period_end": now.isoformat()
        }
    
    async def generate_invoice(self, org_id: str, month: Optional[str] = None) -> Dict:
        """Generate monthly invoice"""
        if month is None:
            month = datetime.utcnow().strftime("%Y-%m")
        
        usage = await self.get_usage_this_month(org_id)
        
        # Get org tier
        org = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org.scalar_one_or_none()
        tier = org.tier if org else "free"
        
        tier_info = self.TIERS.get(tier, self.TIERS["free"])
        
        # Calculate charges
        base_price = tier_info["price"] if isinstance(tier_info["price"], (int, float)) else 0
        llm_cost = usage["llm_cost"]
        total = base_price + llm_cost
        
        return {
            "invoice_id": f"INV-{org_id}-{month}",
            "org_id": org_id,
            "month": month,
            "tier": tier,
            "base_price": base_price,
            "llm_cost": llm_cost,
            "total": total,
            "usage": usage,
            "tier_limits": {
                "max_agents": tier_info["agents"],
                "max_teams": tier_info["teams"],
                "max_logs_gb": tier_info["logs_gb"]
            },
            "status": "generated",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def check_limits(self, org_id: str) -> Dict:
        """Check if org is within tier limits"""
        org = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org.scalar_one_or_none()
        tier = org.tier if org else "free"
        tier_info = self.TIERS.get(tier, self.TIERS["free"])
        
        usage = await self.get_usage_this_month(org_id)
        
        warnings = []
        
        # Check agent limit
        if usage["active_agents"] >= tier_info["agents"]:
            warnings.append(f"Agent limit reached: {usage['active_agents']}/{tier_info['agents']}")
        
        # Check cost alerts
        if tier == "free" and usage["llm_cost"] > 10:
            warnings.append("Free tier cost limit approaching")
        
        return {
            "within_limits": len(warnings) == 0,
            "warnings": warnings,
            "usage": usage,
            "tier": tier,
            "limits": tier_info
        }
