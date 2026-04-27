"""Hierarchy-Aware Escalation for FleetOps Approvals

Routes approval requests to the right approvers based on:
- Org hierarchy
- User roles
- Action type
- Danger level
- Escalation timeouts
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid


@dataclass
class ApproverNode:
    """A person in the approval hierarchy"""
    user_id: str
    name: str
    email: str
    role: str  # "team_lead", "manager", "director", "cto"
    can_approve: List[str]  # Types of actions they can approve
    max_cost_approval: Optional[float] = None
    escalation_timeout_minutes: float = 15.0
    backup_approver_id: Optional[str] = None


class HierarchyEscalation:
    """Manages approval routing through org hierarchy"""
    
    # Default role hierarchy
    ROLE_HIERARCHY = {
        "team_member": {"level": 0, "can_approve": ["read"]},
        "team_lead": {"level": 1, "can_approve": ["read", "test", "deploy_staging"]},
        "manager": {"level": 2, "can_approve": ["read", "write", "deploy_prod", "schema_change"]},
        "director": {"level": 3, "can_approve": ["read", "write", "delete", "deploy_prod", "schema_change", "budget_change"]},
        "cto": {"level": 4, "can_approve": ["*"]},  # Can approve anything
    }
    
    # Escalation timeouts by danger level
    ESCALATION_TIMEOUTS = {
        "safe": None,
        "low": None,
        "medium": 30.0,    # 30 minutes
        "high": 15.0,     # 15 minutes
        "critical": 5.0,  # 5 minutes
    }
    
    def __init__(self, org_hierarchy: Optional[Dict[str, Any]] = None):
        self.hierarchy = org_hierarchy or {}
        self._approvers_cache: Dict[str, ApproverNode] = {}
    
    def find_approvers(
        self,
        action_type: str,
        danger_level: str,
        requester_id: str,
        org_id: str,
        estimated_cost: float = 0.0
    ) -> List[str]:
        """Find appropriate approvers for an action
        
        Returns list of user IDs in priority order (closest first)
        """
        approvers = []
        
        # Get requester's team
        requester_team = self._get_user_team(requester_id, org_id)
        if not requester_team:
            # Fallback: return org-level approvers
            return self._get_org_approvers(org_id, action_type, estimated_cost)
        
        # Primary approver: team lead
        team_lead = self._get_team_lead(requester_team, org_id)
        if team_lead and self._can_approve(team_lead, action_type, estimated_cost):
            approvers.append(team_lead)
        
        # Escalation path based on danger level
        if danger_level in ("high", "critical"):
            # Add manager
            manager = self._get_manager(requester_id, org_id)
            if manager and manager not in approvers:
                approvers.append(manager)
            
            # For critical, add director/CTO
            if danger_level == "critical":
                director = self._get_director(org_id)
                if director and director not in approvers:
                    approvers.append(director)
        
        # If no approvers found in hierarchy, fallback to org-level
        if not approvers:
            approvers = self._get_org_approvers(org_id, action_type, estimated_cost)
        
        return approvers
    
    def calculate_escalation_time(
        self,
        danger_level: str,
        approver_role: Optional[str] = None
    ) -> Optional[float]:
        """Calculate how long before escalating to next level"""
        base_timeout = self.ESCALATION_TIMEOUTS.get(danger_level)
        if not base_timeout:
            return None
        
        # Role-based adjustment
        if approver_role and approver_role in ["cto", "director"]:
            # C-level gets more time for critical decisions
            return base_timeout * 2
        
        return base_timeout
    
    def get_next_escalation_level(
        self,
        current_approver_id: str,
        org_id: str
    ) -> Optional[str]:
        """Get who to escalate to if current approver doesn't respond"""
        current_role = self._get_user_role(current_approver_id, org_id)
        if not current_role:
            return None
        
        current_level = self.ROLE_HIERARCHY.get(current_role, {}).get("level", 0)
        
        # Find next level up
        next_level = current_level + 1
        for user_id, user_info in self._get_org_users(org_id).items():
            role = user_info.get("role", "")
            role_level = self.ROLE_HIERARCHY.get(role, {}).get("level", 0)
            if role_level == next_level:
                return user_id
        
        return None
    
    def _get_user_team(self, user_id: str, org_id: str) -> Optional[str]:
        """Get the team a user belongs to"""
        org = self.hierarchy.get(org_id, {})
        for team_name, team_data in org.get("teams", {}).items():
            if user_id in team_data.get("members", []):
                return team_name
        return None
    
    def _get_team_lead(self, team_name: str, org_id: str) -> Optional[str]:
        """Get the lead of a team"""
        org = self.hierarchy.get(org_id, {})
        team = org.get("teams", {}).get(team_name, {})
        return team.get("lead")
    
    def _get_manager(self, user_id: str, org_id: str) -> Optional[str]:
        """Get the manager of a user"""
        org = self.hierarchy.get(org_id, {})
        users = org.get("users", {})
        user = users.get(user_id, {})
        return user.get("manager_id")
    
    def _get_director(self, org_id: str) -> Optional[str]:
        """Get the director/CTO of the org"""
        org = self.hierarchy.get(org_id, {})
        return org.get("director_id") or org.get("cto_id")
    
    def _get_org_approvers(
        self,
        org_id: str,
        action_type: str,
        estimated_cost: float
    ) -> List[str]:
        """Get org-level approvers as fallback"""
        approvers = []
        org = self.hierarchy.get(org_id, {})
        
        for user_id, user_info in org.get("users", {}).items():
            if self._can_approve_from_info(user_info, action_type, estimated_cost):
                approvers.append(user_id)
        
        return approvers
    
    def _get_user_role(self, user_id: str, org_id: str) -> Optional[str]:
        """Get role of a user"""
        org = self.hierarchy.get(org_id, {})
        user = org.get("users", {}).get(user_id, {})
        return user.get("role")
    
    def _get_org_users(self, org_id: str) -> Dict[str, Any]:
        """Get all users in an org"""
        org = self.hierarchy.get(org_id, {})
        return org.get("users", {})
    
    def _can_approve(
        self,
        approver_id: str,
        action_type: str,
        estimated_cost: float
    ) -> bool:
        """Check if an approver can approve a specific action"""
        user = self._approvers_cache.get(approver_id)
        if not user:
            return False
        
        # Check role permissions
        role_info = self.ROLE_HIERARCHY.get(user.role, {})
        allowed_actions = role_info.get("can_approve", [])
        
        if "*" in allowed_actions:
            return True  # C-level can approve anything
        
        if action_type not in allowed_actions:
            return False
        
        # Check cost limit
        if user.max_cost_approval and estimated_cost > user.max_cost_approval:
            return False
        
        return True
    
    def _can_approve_from_info(
        self,
        user_info: Dict[str, Any],
        action_type: str,
        estimated_cost: float
    ) -> bool:
        """Check approval capability from user info dict"""
        role = user_info.get("role", "")
        role_info = self.ROLE_HIERARCHY.get(role, {})
        allowed_actions = role_info.get("can_approve", [])
        
        if "*" in allowed_actions:
            return True
        
        if action_type not in allowed_actions:
            return False
        
        max_cost = user_info.get("max_cost_approval")
        if max_cost and estimated_cost > max_cost:
            return False
        
        return True


# Global instance
escalation_manager = HierarchyEscalation()


def get_approvers(
    action_type: str,
    danger_level: str,
    requester_id: str,
    org_id: str,
    estimated_cost: float = 0.0
) -> List[str]:
    """Convenience function to find approvers"""
    return escalation_manager.find_approvers(
        action_type=action_type,
        danger_level=danger_level,
        requester_id=requester_id,
        org_id=org_id,
        estimated_cost=estimated_cost
    )
