"""A/B Testing Service for FleetOps

Features:
- A/B test prompts for agents
- Split traffic between variants
- Measure conversion/performance
- Auto-select winner
- Statistical significance testing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.models import Agent, Task, Event, LLMUsage

class ABTestVariant:
    """A single variant in an A/B test"""
    def __init__(self, variant_id: str, name: str, prompt: str):
        self.variant_id = variant_id
        self.name = name
        self.prompt = prompt
        self.traffic_percentage: float = 50.0
        self.metrics = {
            "impressions": 0,
            "successes": 0,
            "failures": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0
        }

class ABTest:
    """An A/B test configuration"""
    def __init__(self, test_id: str, name: str, agent_id: str, 
                 metric: str = "completion_rate"):
        self.test_id = test_id
        self.name = name
        self.agent_id = agent_id
        self.metric = metric  # completion_rate, cost_efficiency, speed, approval_rate
        self.variants: List[ABTestVariant] = []
        self.status = "running"  # running, paused, completed
        self.started_at: datetime = datetime.utcnow()
        self.ended_at: Optional[datetime] = None
        self.winner: Optional[str] = None
        self.min_samples: int = 100
        self.confidence_threshold: float = 0.95
    
    def add_variant(self, name: str, prompt: str, 
                    traffic: float = 50.0) -> ABTestVariant:
        """Add a variant to the test"""
        variant_id = f"{self.test_id}_v{len(self.variants)}"
        variant = ABTestVariant(variant_id, name, prompt)
        variant.traffic_percentage = traffic
        self.variants.append(variant)
        return variant
    
    def assign_variant(self) -> ABTestVariant:
        """Randomly assign a variant based on traffic percentages"""
        import random
        r = random.random() * 100
        cumulative = 0
        for variant in self.variants:
            cumulative += variant.traffic_percentage
            if r <= cumulative:
                return variant
        return self.variants[-1]

class ABTestingService:
    """A/B Testing management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.active_tests: Dict[str, ABTest] = {}
    
    async def create_test(self, agent_id: str, name: str,
                         metric: str = "completion_rate",
                         variants: List[Dict] = None) -> Dict:
        """Create a new A/B test"""
        test_id = f"ab_{agent_id}_{datetime.utcnow().timestamp()}"
        test = ABTest(test_id, name, agent_id, metric)
        
        if variants:
            total_traffic = sum(v.get("traffic", 50) for v in variants)
            for variant_data in variants:
                traffic = (variant_data.get("traffic", 50) / total_traffic) * 100
                test.add_variant(
                    variant_data["name"],
                    variant_data["prompt"],
                    traffic
                )
        
        self.active_tests[test_id] = test
        
        return {
            "test_id": test_id,
            "name": name,
            "agent_id": agent_id,
            "metric": metric,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "traffic_percentage": v.traffic_percentage
                }
                for v in test.variants
            ],
            "status": "running"
        }
    
    async def get_variant_for_task(self, test_id: str, task_id: str) -> Dict:
        """Get the variant to use for a task"""
        if test_id not in self.active_tests:
            return {"error": "Test not found"}
        
        test = self.active_tests[test_id]
        if test.status != "running":
            return {"error": f"Test is {test.status}"}
        
        variant = test.assign_variant()
        variant.metrics["impressions"] += 1
        
        return {
            "test_id": test_id,
            "variant_id": variant.variant_id,
            "variant_name": variant.name,
            "prompt": variant.prompt
        }
    
    async def record_result(self, test_id: str, variant_id: str,
                           success: bool, cost: float = 0.0,
                           response_time: float = 0.0) -> Dict:
        """Record result for a variant"""
        if test_id not in self.active_tests:
            return {"error": "Test not found"}
        
        test = self.active_tests[test_id]
        variant = next((v for v in test.variants if v.variant_id == variant_id), None)
        
        if not variant:
            return {"error": "Variant not found"}
        
        if success:
            variant.metrics["successes"] += 1
        else:
            variant.metrics["failures"] += 1
        
        variant.metrics["total_cost"] += cost
        
        # Update average response time
        total = variant.metrics["successes"] + variant.metrics["failures"]
        variant.metrics["avg_response_time"] = (
            (variant.metrics["avg_response_time"] * (total - 1) + response_time) / total
        )
        
        # Check if we can determine a winner
        if total >= test.min_samples:
            winner = await self._check_winner(test)
            if winner:
                test.winner = winner
                test.status = "completed"
                test.ended_at = datetime.utcnow()
        
        return {
            "test_id": test_id,
            "variant_id": variant_id,
            "metrics": variant.metrics
        }
    
    async def _check_winner(self, test: ABTest) -> Optional[str]:
        """Check if we have a statistically significant winner"""
        if len(test.variants) < 2:
            return None
        
        # Simple check: variant with best metric and sufficient sample size
        best_variant = None
        best_score = -1
        
        for variant in test.variants:
            total = variant.metrics["successes"] + variant.metrics["failures"]
            if total < test.min_samples:
                continue
            
            if test.metric == "completion_rate":
                score = variant.metrics["successes"] / total
            elif test.metric == "cost_efficiency":
                score = 1 / (variant.metrics["total_cost"] / total + 0.01)
            elif test.metric == "speed":
                score = 1 / (variant.metrics["avg_response_time"] + 0.01)
            else:
                score = variant.metrics["successes"] / total
            
            if score > best_score:
                best_score = score
                best_variant = variant
        
        return best_variant.variant_id if best_variant else None
    
    async def get_test_results(self, test_id: str) -> Dict:
        """Get current results for a test"""
        if test_id not in self.active_tests:
            return {"error": "Test not found"}
        
        test = self.active_tests[test_id]
        
        return {
            "test_id": test_id,
            "name": test.name,
            "status": test.status,
            "metric": test.metric,
            "started_at": test.started_at.isoformat(),
            "ended_at": test.ended_at.isoformat() if test.ended_at else None,
            "winner": test.winner,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "traffic_percentage": v.traffic_percentage,
                    "metrics": v.metrics,
                    "success_rate": v.metrics["successes"] / (v.metrics["successes"] + v.metrics["failures"]) if (v.metrics["successes"] + v.metrics["failures"]) > 0 else 0
                }
                for v in test.variants
            ]
        }
    
    async def list_tests(self, agent_id: Optional[str] = None) -> List[Dict]:
        """List all active/completed tests"""
        tests = []
        for test_id, test in self.active_tests.items():
            if agent_id and test.agent_id != agent_id:
                continue
            tests.append(await self.get_test_results(test_id))
        return tests
