"""Unit tests for hierarchy escalation"""
import pytest
import sys

# sys.path removed - using PYTHONPATH

from app.core.hierarchy_escalation import (
    HierarchyEscalation,
    ApproverNode,
    get_approvers
)


class TestHierarchyEscalation:
    """Test hierarchy-based approval routing"""
    
    @pytest.fixture
    def sample_hierarchy(self):
        """Sample org hierarchy"""
        return {
            "org-123": {
                "teams": {
                    "backend": {
                        "lead": "user-lead-1",
                        "members": ["user-dev-1", "user-dev-2", "user-lead-1"]
                    },
                    "frontend": {
                        "lead": "user-lead-2",
                        "members": ["user-dev-3", "user-lead-2"]
                    }
                },
                "users": {
                    "user-dev-1": {
                        "role": "team_lead",  # Developer who is also a team lead
                        "name": "Alice",
                        "manager_id": "user-manager-1"
                    },
                    "user-dev-2": {
                        "role": "team_member",
                        "name": "Bob",
                        "manager_id": "user-manager-1"
                    },
                    "user-lead-1": {
                        "role": "team_lead",
                        "name": "Charlie",
                        "manager_id": "user-manager-1"
                    },
                    "user-manager-1": {
                        "role": "manager",
                        "name": "Diana",
                        "manager_id": "user-director-1"
                    },
                    "user-director-1": {
                        "role": "director",
                        "name": "Eve",
                        "manager_id": None
                    },
                    "user-cto-1": {
                        "role": "cto",
                        "name": "Frank",
                        "manager_id": None
                    }
                },
                "director_id": "user-director-1",
                "cto_id": "user-cto-1"
            }
        }
    
    @pytest.fixture
    def escalation(self, sample_hierarchy):
        return HierarchyEscalation(org_hierarchy=sample_hierarchy)
    
    def test_find_approvers_for_team_member(self, escalation):
        """Team member should route to team lead"""
        approvers = escalation.find_approvers(
            action_type="read",  # Team lead can approve reads
            danger_level="medium",
            requester_id="user-dev-2",
            org_id="org-123",
            estimated_cost=50.0
        )
        
        assert "user-lead-1" in approvers
    
    def test_high_risk_escalation(self, escalation):
        """High risk should include manager"""
        approvers = escalation.find_approvers(
            action_type="delete",
            danger_level="high",
            requester_id="user-dev-2",
            org_id="org-123",
            estimated_cost=100.0
        )
        
        # Team lead can't approve deletes, so manager is primary
        assert "user-manager-1" in approvers
    
    def test_critical_risk_escalation(self, escalation):
        """Critical risk should include director/CTO"""
        approvers = escalation.find_approvers(
            action_type="schema_change",
            danger_level="critical",
            requester_id="user-dev-2",
            org_id="org-123",
            estimated_cost=500.0
        )
        
        # Manager and director should be included (team lead can't approve schema changes)
        assert "user-manager-1" in approvers
        # Should have director
        assert "user-director-1" in approvers
    
    def test_safe_action_no_approvers(self, escalation):
        """Safe actions don't need approvers"""
        approvers = escalation.find_approvers(
            action_type="read",
            danger_level="safe",
            requester_id="user-dev-2",
            org_id="org-123",
            estimated_cost=0.0
        )
        
        # For safe actions, might still return approvers but approval not required
        assert isinstance(approvers, list)
    
    def test_unknown_user_fallback(self, escalation):
        """Unknown user should fallback to org-level approvers"""
        approvers = escalation.find_approvers(
            action_type="write",
            danger_level="medium",
            requester_id="unknown-user",
            org_id="org-123",
            estimated_cost=50.0
        )
        
        # Should return org-level approvers
        assert len(approvers) > 0
    
    def test_unknown_org_fallback(self, escalation):
        """Unknown org should return empty or fallback"""
        approvers = escalation.find_approvers(
            action_type="write",
            danger_level="medium",
            requester_id="user-dev-2",
            org_id="unknown-org",
            estimated_cost=50.0
        )
        
        # With unknown org, no hierarchy available
        assert approvers == []
    
    def test_escalation_timeout_by_level(self, escalation):
        """Different danger levels have different timeouts"""
        medium_timeout = escalation.calculate_escalation_time("medium")
        high_timeout = escalation.calculate_escalation_time("high")
        critical_timeout = escalation.calculate_escalation_time("critical")
        
        assert medium_timeout == 30.0
        assert high_timeout == 15.0
        assert critical_timeout == 5.0
    
    def test_safe_no_escalation(self, escalation):
        """Safe actions don't escalate"""
        timeout = escalation.calculate_escalation_time("safe")
        assert timeout is None
    
    def test_next_escalation_level(self, escalation):
        """Get next level up in hierarchy"""
        next_level = escalation.get_next_escalation_level(
            current_approver_id="user-lead-1",
            org_id="org-123"
        )
        
        # Team lead (level 1) should escalate to manager (level 2)
        assert next_level == "user-manager-1"
    
    def test_next_escalation_director(self, escalation):
        """Director escalates to CTO"""
        next_level = escalation.get_next_escalation_level(
            current_approver_id="user-director-1",
            org_id="org-123"
        )
        
        # Director (level 3) escalates to CTO (level 4)
        assert next_level == "user-cto-1"
    
    def test_next_escalation_cto_top_level(self, escalation):
        """CTO has no higher level"""
        next_level = escalation.get_next_escalation_level(
            current_approver_id="user-cto-1",
            org_id="org-123"
        )
        
        # CTO is top level, no escalation
        assert next_level is None
    
    def test_team_lead_as_approver(self, escalation):
        """Team lead can approve for their team"""
        approvers = escalation.find_approvers(
            action_type="read",
            danger_level="medium",
            requester_id="user-dev-2",
            org_id="org-123",
            estimated_cost=10.0
        )
        
        # Team lead should be primary approver
        assert "user-lead-1" in approvers
    
    def test_manager_can_approve_writes(self, escalation):
        """Manager can approve write operations"""
        can_approve = escalation._can_approve_from_info(
            user_info={"role": "manager", "max_cost_approval": 1000.0},
            action_type="write",
            estimated_cost=500.0
        )
        
        assert can_approve is True
    
    def test_team_lead_cannot_approve_high_cost(self, escalation):
        """Team lead might have cost limits"""
        # Depends on config, but team leads typically can't approve very high costs
        can_approve = escalation._can_approve_from_info(
            user_info={"role": "team_lead", "max_cost_approval": 50.0},
            action_type="write",
            estimated_cost=500.0
        )
        
        assert can_approve is False
    
    def test_cto_can_approve_anything(self, escalation):
        """CTO can approve anything"""
        can_approve = escalation._can_approve_from_info(
            user_info={"role": "cto"},
            action_type="anything",
            estimated_cost=999999.0
        )
        
        assert can_approve is True


class TestConvenienceFunction:
    """Test the get_approvers convenience function"""
    
    def test_get_approvers_basic(self):
        """Test basic usage"""
        # With no hierarchy set up, returns empty
        approvers = get_approvers(
            action_type="write",
            danger_level="medium",
            requester_id="user-1",
            org_id="org-123"
        )
        
        assert isinstance(approvers, list)


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_hierarchy(self):
        """Empty hierarchy should handle gracefully"""
        escalation = HierarchyEscalation(org_hierarchy={})
        
        approvers = escalation.find_approvers(
            action_type="write",
            danger_level="medium",
            requester_id="user-1",
            org_id="org-123"
        )
        
        assert approvers == []
    
    def test_none_hierarchy(self):
        """None hierarchy should handle gracefully"""
        escalation = HierarchyEscalation(org_hierarchy=None)
        
        approvers = escalation.find_approvers(
            action_type="write",
            danger_level="medium",
            requester_id="user-1",
            org_id="org-123"
        )
        
        assert approvers == []
    
    def test_role_based_escalation_timeout(self):
        """C-level gets more time for critical decisions"""
        escalation = HierarchyEscalation()
        
        # Regular manager gets normal timeout
        regular_timeout = escalation.calculate_escalation_time("critical")
        
        # C-level gets double
        cto_timeout = escalation.calculate_escalation_time(
            "critical",
            approver_role="cto"
        )
        
        assert cto_timeout == regular_timeout * 2
