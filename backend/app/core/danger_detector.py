"""Danger Detection Engine for FleetOps Approval Flow

Determines what actions are dangerous based on:
- Tool type
- Action arguments
- File patterns
- Environment
- Cost thresholds
- Organizational rules
"""

from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from enum import Enum
import re


class DangerLevel(Enum):
    """Risk classification levels"""
    SAFE = "safe"          # 🟢 No approval needed
    LOW = "low"            # 🟡 Log only
    MEDIUM = "medium"      # 🟠 Needs 1 approver
    HIGH = "high"           # 🔴 Needs 1 approver + notification
    CRITICAL = "critical"   # 🚨 Needs 2 approvers + escalation


@dataclass
class DangerRule:
    """A rule that defines when something is dangerous"""
    name: str
    description: str
    danger_level: DangerLevel
    conditions: Dict[str, Any]  # Conditions that trigger this rule
    applies_to: Optional[Set[str]] = None  # Which orgs this applies to


class DangerDetector:
    """Analyzes agent actions and assigns danger levels"""
    
    # Default built-in rules
    DEFAULT_RULES: List[DangerRule] = [
        # Tool-based rules
        DangerRule(
            name="bash_execution",
            description="Executing shell commands is always dangerous",
            danger_level=DangerLevel.HIGH,
            conditions={"tool": "bash", "contains": ["rm", "dd", ">"]},
        ),
        DangerRule(
            name="bash_read",
            description="Safe bash commands",
            danger_level=DangerLevel.LOW,
            conditions={"tool": "bash", "contains": ["ls", "cat", "echo"]},
        ),
        DangerRule(
            name="file_delete",
            description="Deleting files",
            danger_level=DangerLevel.HIGH,
            conditions={"tool": "write", "contains": ["DELETE", "rm", "rmdir"]},
        ),
        DangerRule(
            name="database_write",
            description="Writing to database",
            danger_level=DangerLevel.HIGH,
            conditions={"tool": "db", "contains": ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]},
        ),
        DangerRule(
            name="database_read",
            description="Reading from database is medium risk",
            danger_level=DangerLevel.MEDIUM,
            conditions={"tool": "db", "contains": ["SELECT"]},
        ),
        DangerRule(
            name="external_api",
            description="Calling external APIs",
            danger_level=DangerLevel.MEDIUM,
            conditions={"tool": "api", "contains": ["POST", "PUT", "DELETE", "PATCH"]},
        ),
        DangerRule(
            name="external_api_read",
            description="Safe external API calls",
            danger_level=DangerLevel.LOW,
            conditions={"tool": "api", "contains": ["GET"]},
        ),
        # File pattern rules
        DangerRule(
            name="production_config",
            description="Modifying production config files",
            danger_level=DangerLevel.CRITICAL,
            conditions={"path_matches": r".*\.(env|config|prod|production).*"},
        ),
        DangerRule(
            name="auth_files",
            description="Modifying authentication code",
            danger_level=DangerLevel.HIGH,
            conditions={"path_matches": r".*(auth|login|password|secret|token|credential).*"},
        ),
        DangerRule(
            name="infrastructure",
            description="Modifying infrastructure files",
            danger_level=DangerLevel.CRITICAL,
            conditions={"path_matches": r".*(docker-compose|terraform|kubernetes|k8s|\.tf|\.yaml|\.yml).*"},
        ),
        # Environment rules
        DangerRule(
            name="prod_environment",
            description="Any action in production is higher risk",
            danger_level=DangerLevel.HIGH,
            conditions={"environment": "production"},
        ),
    ]
    
    def __init__(self, org_id: Optional[str] = None, custom_rules: Optional[List[DangerRule]] = None):
        self.org_id = org_id
        self.rules: List[DangerRule] = custom_rules or self.DEFAULT_RULES.copy()
    
    def analyze(
        self,
        tool: str,
        arguments: Optional[str] = None,
        file_path: Optional[str] = None,
        environment: str = "development",
        estimated_cost: Optional[float] = None,
        estimated_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze an action and determine danger level
        
        Returns:
            {
                "danger_level": "safe|low|medium|high|critical",
                "score": float,  # 0-1 danger score
                "matched_rules": ["rule_name", ...],
                "details": str,
                "requires_approval": bool,
                "approver_count": int,
                "escalate_after_minutes": Optional[float]
            }
        """
        matched_rules = []
        highest_danger = DangerLevel.SAFE
        details = []
        
        for rule in self.rules:
            if not self._rule_applies(rule, tool, arguments, file_path, environment):
                continue
            
            matched_rules.append(rule.name)
            details.append(rule.description)
            
            # Keep highest danger level
            if self._danger_rank(rule.danger_level) > self._danger_rank(highest_danger):
                highest_danger = rule.danger_level
        
        # Cost-based escalation
        if estimated_cost and estimated_cost > 50.0:
            matched_rules.append("cost_threshold")
            details.append(f"High cost: ${estimated_cost:.2f}")
            if self._danger_rank(highest_danger) < self._danger_rank(DangerLevel.MEDIUM):
                highest_danger = DangerLevel.MEDIUM
        
        if estimated_cost and estimated_cost > 200.0:
            if self._danger_rank(highest_danger) < self._danger_rank(DangerLevel.HIGH):
                highest_danger = DangerLevel.HIGH
        
        # Determine approver requirements
        requires_approval = highest_danger in (DangerLevel.MEDIUM, DangerLevel.HIGH, DangerLevel.CRITICAL)
        approver_count = {
            DangerLevel.SAFE: 0,
            DangerLevel.LOW: 0,
            DangerLevel.MEDIUM: 1,
            DangerLevel.HIGH: 1,
            DangerLevel.CRITICAL: 2,
        }.get(highest_danger, 0)
        
        escalate_after = None
        if highest_danger == DangerLevel.HIGH:
            escalate_after = 15.0  # 15 minutes
        elif highest_danger == DangerLevel.CRITICAL:
            escalate_after = 5.0   # 5 minutes
        
        return {
            "danger_level": highest_danger.value,
            "score": self._calculate_score(highest_danger),
            "matched_rules": matched_rules,
            "details": " | ".join(details) if details else "No danger detected",
            "requires_approval": requires_approval,
            "approver_count": approver_count,
            "escalate_after_minutes": escalate_after,
            "tool": tool,
            "arguments": arguments,
            "environment": environment
        }
    
    def _rule_applies(
        self,
        rule: DangerRule,
        tool: str,
        arguments: Optional[str],
        file_path: Optional[str],
        environment: str
    ) -> bool:
        """Check if a rule applies to the current context"""
        conditions = rule.conditions
        
        # Check tool condition
        if "tool" in conditions and tool != conditions["tool"]:
            return False
        
        # Check contains condition (in arguments)
        if "contains" in conditions:
            if not arguments:
                return False
            if not any(keyword in arguments for keyword in conditions["contains"]):
                return False
        
        # Check path pattern
        if "path_matches" in conditions:
            if not file_path:
                return False
            if not re.search(conditions["path_matches"], file_path, re.IGNORECASE):
                return False
        
        # Check environment
        if "environment" in conditions and environment != conditions["environment"]:
            return False
        
        return True
    
    def _danger_rank(self, level: DangerLevel) -> int:
        """Get numeric rank for comparison"""
        ranks = {
            DangerLevel.SAFE: 0,
            DangerLevel.LOW: 1,
            DangerLevel.MEDIUM: 2,
            DangerLevel.HIGH: 3,
            DangerLevel.CRITICAL: 4,
        }
        return ranks.get(level, 0)
    
    def _calculate_score(self, level: DangerLevel) -> float:
        """Calculate danger score (0-1)"""
        scores = {
            DangerLevel.SAFE: 0.0,
            DangerLevel.LOW: 0.25,
            DangerLevel.MEDIUM: 0.5,
            DangerLevel.HIGH: 0.75,
            DangerLevel.CRITICAL: 1.0,
        }
        return scores.get(level, 0.0)
    
    def add_rule(self, rule: DangerRule) -> None:
        """Add a custom rule to the detector"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False


# Global instance
danger_detector = DangerDetector()


def analyze_action(
    tool: str,
    arguments: Optional[str] = None,
    file_path: Optional[str] = None,
    environment: str = "development",
    estimated_cost: Optional[float] = None,
    estimated_tokens: Optional[int] = None,
    org_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to analyze an action"""
    detector = DangerDetector(org_id=org_id) if org_id else danger_detector
    return detector.analyze(
        tool=tool,
        arguments=arguments,
        file_path=file_path,
        environment=environment,
        estimated_cost=estimated_cost,
        estimated_tokens=estimated_tokens
    )
