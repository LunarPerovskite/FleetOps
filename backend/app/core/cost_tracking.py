"""Advanced Cost Tracking System for FleetOps

Handles multiple pricing models:
- Pay-per-token APIs (OpenAI, Anthropic, Groq, etc.)
- Subscription services (Claude Pro, Copilot, etc.)
- Local compute (Ollama, vLLM - electricity/hardware cost)
- Aggregator services (OpenRouter used by other agents)
- Hybrid deployments (some local, some cloud)

Tracks:
- Direct API costs
- Subscription usage allocation
- Estimated compute costs
- Nested service costs (when agents call other services)
- Cost attribution per agent/task/user
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import json


class PricingModel(str, Enum):
    """Different pricing models for AI services"""
    PAY_PER_TOKEN = "pay_per_token"      # Standard API pricing
    SUBSCRIPTION = "subscription"         # Monthly/annual fee
    PAY_PER_HOUR = "pay_per_hour"         # Compute time (cloud GPUs)
    FREE_LOCAL = "free_local"             # Local hardware only
    HYBRID = "hybrid"                     # Mix of above
    AGGREGATOR = "aggregator"             # OpenRouter, etc.


class SubscriptionTier(str, Enum):
    """Subscription tiers"""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


@dataclass
class PricingConfig:
    """Configuration for a service's pricing"""
    model: PricingModel
    # Pay-per-token rates (per 1K tokens)
    input_rate: Optional[Decimal] = None
    output_rate: Optional[Decimal] = None
    # Subscription
    monthly_cost: Optional[Decimal] = None
    annual_cost: Optional[Decimal] = None
    included_tokens: int = 0  # Tokens included in subscription
    # Pay-per-hour
    hourly_rate: Optional[Decimal] = None
    # Local compute estimate
    kwh_per_hour: Optional[Decimal] = None  # Power consumption
    electricity_rate: Decimal = Decimal("0.15")  # $/kWh default
    hardware_cost_per_hour: Optional[Decimal] = None  # GPU rental/amortized
    # Aggregator markup
    base_cost_multiplier: Decimal = Decimal("1.0")
    # Metadata
    currency: str = "USD"
    
    def calculate_subscription_cost(self, tokens_used: int) -> Decimal:
        """Calculate cost for subscription model with included tokens"""
        if self.model != PricingModel.SUBSCRIPTION:
            return Decimal("0")
        
        if tokens_used <= self.included_tokens:
            return Decimal("0")  # Within included limit
        
        # Calculate overage (if applicable)
        overage_tokens = tokens_used - self.included_tokens
        # Default overage rate: $0.01 per 1K tokens
        overage_rate = Decimal("0.01")
        return (Decimal(overage_tokens) / 1000) * overage_rate
    
    def calculate_local_cost(self, hours_running: float) -> Decimal:
        """Estimate cost for local compute (electricity + hardware)"""
        if self.model != PricingModel.FREE_LOCAL:
            return Decimal("0")
        
        # Electricity cost
        kwh = (self.kwh_per_hour or Decimal("0.5")) * Decimal(str(hours_running))
        electricity_cost = kwh * self.electricity_rate
        
        # Hardware cost (if renting/cloud GPU)
        hw_cost = (self.hardware_cost_per_hour or Decimal("0")) * Decimal(str(hours_running))
        
        return electricity_cost + hw_cost


# ═══════════════════════════════════════
# PRICING CONFIGURATIONS
# ═══════════════════════════════════════

PRICING_CONFIGS: Dict[str, PricingConfig] = {
    # Pay-per-token APIs
    "openai_gpt4": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.03"),
        output_rate=Decimal("0.06")
    ),
    "openai_gpt4_turbo": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.01"),
        output_rate=Decimal("0.03")
    ),
    "openai_gpt35": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.0005"),
        output_rate=Decimal("0.0015")
    ),
    "anthropic_claude_opus": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.015"),
        output_rate=Decimal("0.075")
    ),
    "anthropic_claude_sonnet": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.003"),
        output_rate=Decimal("0.015")
    ),
    "anthropic_claude_haiku": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.00025"),
        output_rate=Decimal("0.00125")
    ),
    "groq_llama3_8b": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.0001"),
        output_rate=Decimal("0.0001")
    ),
    "groq_llama3_70b": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.0006"),
        output_rate=Decimal("0.0008")
    ),
    "groq_mixtral": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.0003"),
        output_rate=Decimal("0.0005")
    ),
    "perplexity_sonar": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.0005"),
        output_rate=Decimal("0.0015")
    ),
    "perplexity_sonar_pro": PricingConfig(
        model=PricingModel.PAY_PER_TOKEN,
        input_rate=Decimal("0.003"),
        output_rate=Decimal("0.015")
    ),
    
    # Subscription services
    "claude_pro": PricingConfig(
        model=PricingModel.SUBSCRIPTION,
        monthly_cost=Decimal("20.00"),
        included_tokens=0  # Actually unlimited, but we track usage
    ),
    "github_copilot_individual": PricingConfig(
        model=PricingModel.SUBSCRIPTION,
        monthly_cost=Decimal("10.00"),
        annual_cost=Decimal("100.00")
    ),
    "github_copilot_business": PricingConfig(
        model=PricingModel.SUBSCRIPTION,
        monthly_cost=Decimal("19.00"),
    ),
    "cursor_pro": PricingConfig(
        model=PricingModel.SUBSCRIPTION,
        monthly_cost=Decimal("20.00"),
    ),
    "cursor_business": PricingConfig(
        model=PricingModel.SUBSCRIPTION,
        monthly_cost=Decimal("40.00"),
        included_tokens=500000  # 500K fast requests
    ),
    
    # Local models (estimated compute cost)
    "ollama_local": PricingConfig(
        model=PricingModel.FREE_LOCAL,
        kwh_per_hour=Decimal("0.3"),  # RTX 4090 ~300W
        electricity_rate=Decimal("0.15")
    ),
    "vllm_local": PricingConfig(
        model=PricingModel.FREE_LOCAL,
        kwh_per_hour=Decimal("0.4"),  # Multi-GPU
        electricity_rate=Decimal("0.15")
    ),
    "ollama_cloud": PricingConfig(  # Cloud-hosted Ollama
        model=PricingModel.PAY_PER_HOUR,
        hourly_rate=Decimal("2.00")  # Estimated cloud GPU cost
    ),
    
    # Aggregator (adds markup)
    "openrouter_default": PricingConfig(
        model=PricingModel.AGGREGATOR,
        base_cost_multiplier=Decimal("1.1")  # 10% markup
    ),
}


@dataclass
class CostEntry:
    """Single cost entry"""
    timestamp: str
    service: str
    model: str
    agent_id: str
    task_id: str
    user_id: Optional[str] = None
    
    # Token usage (for API models)
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Compute (for local/cloud)
    compute_seconds: float = 0.0
    
    # Subscription allocation
    subscription_minutes_used: float = 0.0
    
    # Costs
    api_cost: Decimal = Decimal("0")
    compute_cost: Decimal = Decimal("0")
    subscription_allocation: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    
    # Metadata
    pricing_model: PricingModel = PricingModel.PAY_PER_TOKEN
    notes: Optional[str] = None
    nested_services: List[Dict] = field(default_factory=list)


class CostTracker:
    """Advanced cost tracking with multiple pricing models"""
    
    def __init__(self):
        self.entries: List[CostEntry] = []
        self.budgets: Dict[str, Decimal] = {}  # task_id -> max budget
        self.alerts_sent: set = set()
        
        # Track subscription usage (shared across tasks)
        self.subscription_usage: Dict[str, Dict] = defaultdict(lambda: {
            "total_tokens": 0,
            "total_minutes": 0,
            "allocated_cost": Decimal("0"),
            "last_reset": datetime.utcnow().isoformat()
        })
    
    def track_api_cost(self, service: str, model: str,
                      agent_id: str, task_id: str,
                      input_tokens: int, output_tokens: int,
                      user_id: Optional[str] = None,
                      nested_services: Optional[List[Dict]] = None) -> CostEntry:
        """Track cost for pay-per-token API"""
        
        # Find pricing config
        config_key = f"{service}_{model}".lower().replace("-", "_").replace(".", "_")
        config = PRICING_CONFIGS.get(config_key)
        
        if not config:
            # Fallback to generic rates
            config = PricingConfig(
                model=PricingModel.PAY_PER_TOKEN,
                input_rate=Decimal("0.001"),
                output_rate=Decimal("0.002")
            )
        
        # Calculate cost
        input_cost = (Decimal(input_tokens) / 1000) * (config.input_rate or Decimal("0"))
        output_cost = (Decimal(output_tokens) / 1000) * (config.output_rate or Decimal("0"))
        api_cost = input_cost + output_cost
        
        # Handle aggregator markup
        if config.model == PricingModel.AGGREGATOR:
            api_cost = api_cost * config.base_cost_multiplier
        
        entry = CostEntry(
            timestamp=datetime.utcnow().isoformat(),
            service=service,
            model=model,
            agent_id=agent_id,
            task_id=task_id,
            user_id=user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            api_cost=api_cost.quantize(Decimal("0.000001")),
            total_cost=api_cost.quantize(Decimal("0.000001")),
            pricing_model=config.model,
            nested_services=nested_services or []
        )
        
        self.entries.append(entry)
        
        # Check budget
        self._check_budget(task_id)
        
        return entry
    
    def track_subscription_usage(self, service: str, model: str,
                                agent_id: str, task_id: str,
                                tokens_used: int = 0,
                                minutes_used: float = 0,
                                user_id: Optional[str] = None) -> CostEntry:
        """Track usage against a subscription ( Claude Pro, Copilot, etc.)"""
        
        config_key = f"{service}_{model}".lower().replace("-", "_")
        config = PRICING_CONFIGS.get(config_key, PricingConfig(
            model=PricingModel.SUBSCRIPTION,
            monthly_cost=Decimal("20.00")
        ))
        
        # Update subscription usage
        sub_key = f"{service}_{user_id or 'shared'}"
        self.subscription_usage[sub_key]["total_tokens"] += tokens_used
        self.subscription_usage[sub_key]["total_minutes"] += minutes_used
        
        # Calculate allocated cost (amortized)
        # For unlimited subscriptions, we estimate cost based on usage intensity
        monthly_cost = config.monthly_cost or Decimal("0")
        
        # Simple allocation: cost per minute of usage
        # Assuming 160 hours/month of active usage for $20 = $0.002/minute
        allocated_cost = Decimal(str(minutes_used)) * (monthly_cost / 10000)
        
        self.subscription_usage[sub_key]["allocated_cost"] += allocated_cost
        
        entry = CostEntry(
            timestamp=datetime.utcnow().isoformat(),
            service=service,
            model=model,
            agent_id=agent_id,
            task_id=task_id,
            user_id=user_id,
            input_tokens=tokens_used,
            subscription_minutes_used=minutes_used,
            subscription_allocation=allocated_cost.quantize(Decimal("0.000001")),
            total_cost=allocated_cost.quantize(Decimal("0.000001")),
            pricing_model=PricingModel.SUBSCRIPTION,
            notes=f"Subscription usage - {sub_key}"
        )
        
        self.entries.append(entry)
        return entry
    
    def track_local_compute(self, service: str, model: str,
                           agent_id: str, task_id: str,
                           compute_seconds: float,
                           hardware_type: str = "gpu_rtx4090",
                           user_id: Optional[str] = None) -> CostEntry:
        """Track cost for local compute (electricity + hardware amortization)"""
        
        config = PRICING_CONFIGS.get(f"{service}_local", PricingConfig(
            model=PricingModel.FREE_LOCAL,
            kwh_per_hour=Decimal("0.3"),
            electricity_rate=Decimal("0.15")
        ))
        
        hours = compute_seconds / 3600
        compute_cost = config.calculate_local_cost(hours)
        
        entry = CostEntry(
            timestamp=datetime.utcnow().isoformat(),
            service=service,
            model=model,
            agent_id=agent_id,
            task_id=task_id,
            user_id=user_id,
            compute_seconds=compute_seconds,
            compute_cost=compute_cost.quantize(Decimal("0.000001")),
            total_cost=compute_cost.quantize(Decimal("0.000001")),
            pricing_model=PricingModel.FREE_LOCAL,
            notes=f"Local compute on {hardware_type}"
        )
        
        self.entries.append(entry)
        return entry
    
    def track_nested_service(self, parent_service: str, parent_task_id: str,
                            child_service: str, child_cost: Decimal,
                            child_tokens: Dict[str, int]) -> None:
        """Track when an agent uses another service internally"""
        # This gets added as metadata to the parent service's cost entry
        # Find the most recent entry for this task
        for entry in reversed(self.entries):
            if entry.task_id == parent_task_id and entry.service == parent_service:
                entry.nested_services.append({
                    "service": child_service,
                    "cost": str(child_cost),
                    "tokens": child_tokens
                })
                # Add to total cost
                entry.total_cost += child_cost
                break
    
    def set_budget(self, task_id: str, max_cost_usd: float):
        """Set budget limit for a task"""
        self.budgets[task_id] = Decimal(str(max_cost_usd))
        self.alerts_sent.discard(task_id)  # Reset alerts
    
    def _check_budget(self, task_id: str):
        """Check if approaching or exceeding budget"""
        budget = self.budgets.get(task_id)
        if not budget:
            return
        
        spent = self.get_task_cost(task_id)
        percent = float((spent / budget) * 100)
        
        # Alert thresholds
        if percent >= 100 and f"{task_id}_exceeded" not in self.alerts_sent:
            self.alerts_sent.add(f"{task_id}_exceeded")
            # In production, send alert (email, webhook, etc.)
            print(f"🚨 ALERT: Task {task_id} exceeded budget! ${spent} / ${budget}")
        
        elif percent >= 80 and f"{task_id}_warning" not in self.alerts_sent:
            self.alerts_sent.add(f"{task_id}_warning")
            print(f"⚠️ WARNING: Task {task_id} at {percent:.1f}% of budget (${spent} / ${budget})")
    
    def get_task_cost(self, task_id: str) -> Decimal:
        """Get total cost for a task"""
        return sum(
            entry.total_cost for entry in self.entries
            if entry.task_id == task_id
        )
    
    def get_agent_cost(self, agent_id: str) -> Decimal:
        """Get total cost for an agent"""
        return sum(
            entry.total_cost for entry in self.entries
            if entry.agent_id == agent_id
        )
    
    def get_user_cost(self, user_id: str) -> Dict:
        """Get cost summary for a user"""
        entries = [e for e in self.entries if e.user_id == user_id]
        
        by_service = defaultdict(lambda: {"cost": Decimal("0"), "tokens": 0})
        for e in entries:
            by_service[e.service]["cost"] += e.total_cost
            by_service[e.service]["tokens"] += e.input_tokens + e.output_tokens
        
        return {
            "user_id": user_id,
            "total_cost": str(sum(e.total_cost for e in entries)),
            "total_requests": len(entries),
            "by_service": {
                k: {
                    "cost": str(v["cost"]),
                    "total_tokens": v["tokens"]
                }
                for k, v in by_service.items()
            }
        }
    
    def get_summary(self, period: Optional[str] = None) -> Dict:
        """Get cost summary for a period (day, week, month) or all time"""
        entries = self.entries
        
        if period:
            now = datetime.utcnow()
            if period == "day":
                cutoff = now - timedelta(days=1)
            elif period == "week":
                cutoff = now - timedelta(weeks=1)
            elif period == "month":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = now - timedelta(days=1)
            
            entries = [
                e for e in entries
                if datetime.fromisoformat(e.timestamp) > cutoff
            ]
        
        # Breakdown by pricing model
        by_model = defaultdict(lambda: {"cost": Decimal("0"), "count": 0})
        for e in entries:
            by_model[e.pricing_model.value]["cost"] += e.total_cost
            by_model[e.pricing_model.value]["count"] += 1
        
        # Breakdown by service
        by_service = defaultdict(lambda: {"cost": Decimal("0"), "tokens": 0})
        for e in entries:
            by_service[e.service]["cost"] += e.total_cost
            by_service[e.service]["tokens"] += e.input_tokens + e.output_tokens
        
        return {
            "period": period or "all_time",
            "total_cost": str(sum(e.total_cost for e in entries)),
            "total_requests": len(entries),
            "total_tokens": sum(e.input_tokens + e.output_tokens for e in entries),
            "by_pricing_model": {
                k: {
                    "cost": str(v["cost"]),
                    "request_count": v["count"]
                }
                for k, v in by_model.items()
            },
            "by_service": {
                k: {
                    "cost": str(v["cost"]),
                    "total_tokens": v["tokens"]
                }
                for k, v in by_service.items()
            }
        }
    
    def get_detailed_report(self, task_id: Optional[str] = None) -> List[Dict]:
        """Get detailed cost entries"""
        entries = self.entries
        if task_id:
            entries = [e for e in entries if e.task_id == task_id]
        
        return [
            {
                "timestamp": e.timestamp,
                "service": e.service,
                "model": e.model,
                "agent_id": e.agent_id,
                "task_id": e.task_id,
                "input_tokens": e.input_tokens,
                "output_tokens": e.output_tokens,
                "compute_seconds": e.compute_seconds,
                "api_cost": str(e.api_cost),
                "compute_cost": str(e.compute_cost),
                "subscription_allocation": str(e.subscription_allocation),
                "total_cost": str(e.total_cost),
                "pricing_model": e.pricing_model.value,
                "nested_services": e.nested_services,
                "notes": e.notes
            }
            for e in entries
        ]
    
    def export_to_json(self, filename: str):
        """Export cost data to JSON"""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "summary": self.get_summary(),
            "entries": self.get_detailed_report()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)


# Global cost tracker instance
cost_tracker = CostTracker()


# ═══════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════

"""
# 1. Track API cost (OpenAI, Anthropic, etc.)
cost_tracker.track_api_cost(
    service="openai",
    model="gpt-4",
    agent_id="claude_code_01",
    task_id="task_123",
    input_tokens=1000,
    output_tokens=500,
    user_id="user_456"
)

# 2. Track subscription usage (Claude Pro, Copilot)
cost_tracker.track_subscription_usage(
    service="claude_pro",
    model="claude-3-opus",
    agent_id="claude_code_01",
    task_id="task_123",
    tokens_used=5000,
    minutes_used=10,
    user_id="user_456"
)

# 3. Track local compute (Ollama)
cost_tracker.track_local_compute(
    service="ollama",
    model="llama3",
    agent_id="local_agent_01",
    task_id="task_123",
    compute_seconds=120,
    hardware_type="gpu_rtx4090"
)

# 4. Track nested service (OpenRouter via Roo Code)
cost_tracker.track_api_cost(
    service="openrouter",
    model="anthropic/claude-3.5-sonnet",
    agent_id="roo_code_01",
    task_id="task_123",
    input_tokens=2000,
    output_tokens=1000,
    nested_services=[{
        "service": "anthropic",
        "model": "claude-3.5-sonnet",
        "cost": "0.009",
        "tokens": {"input": 2000, "output": 1000}
    }]
)

# 5. Set budget and check
cost_tracker.set_budget("task_123", 5.00)  # $5 budget
summary = cost_tracker.get_summary()
print(f"Total cost: ${summary['total_cost']}")
"""
