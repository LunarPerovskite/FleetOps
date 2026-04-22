"""Integration tests for FleetOps API endpoints

Tests the full request/response flow
"""

import pytest
import uuid
from datetime import datetime, timedelta

# Test data
TEST_USER = {
    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
    "password": "test_password_123",
    "name": "Test User",
    "org_name": "Test Org"
}

test_org_id = None
test_user_id = None
test_token = None
test_task_id = None
test_agent_id = None

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        global test_org_id, test_user_id
        
        response = client.post("/auth/register", json=TEST_USER)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == TEST_USER["email"]
        
        test_org_id = data["user"]["org_id"]
        test_user_id = data["user"]["id"]
    
    def test_login_user(self, client):
        """Test user login"""
        global test_token
        
        response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        test_token = data["access_token"]
    
    def test_get_current_user(self, client):
        """Test get current user"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER["email"]
    
    def test_invalid_login(self, client):
        """Test login with wrong password"""
        response = client.post("/auth/login", json={
            "email": TEST_USER["email"],
            "password": "wrong_password"
        })
        
        assert response.status_code == 401

class TestTaskEndpoints:
    """Test task management endpoints"""
    
    def test_create_task(self, client):
        """Test task creation"""
        global test_task_id
        
        response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "description": "Test Description",
                "agent_id": "agent_test",
                "org_id": test_org_id,
                "risk_level": "low"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        
        test_task_id = data["task_id"]
    
    def test_list_tasks(self, client):
        """Test task listing"""
        response = client.get(
            "/tasks",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) >= 1
    
    def test_get_task(self, client):
        """Test get single task"""
        response = client.get(
            f"/tasks/{test_task_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task_id
    
    def test_approve_task(self, client):
        """Test task approval"""
        response = client.post(
            f"/tasks/{test_task_id}/approve",
            json={
                "decision": "approve",
                "comments": "Looks good",
                "human_id": test_user_id
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code in [200, 201]

class TestAgentEndpoints:
    """Test agent management endpoints"""
    
    def test_create_agent(self, client):
        """Test agent creation"""
        global test_agent_id
        
        response = client.post(
            "/agents",
            json={
                "name": "Test Agent",
                "provider": "claude",
                "model": "claude-3-sonnet",
                "capabilities": ["coding", "analysis"],
                "level": "junior",
                "org_id": test_org_id
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        
        test_agent_id = data["agent_id"]
    
    def test_list_agents(self, client):
        """Test agent listing"""
        response = client.get(
            "/agents",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
    
    def test_update_agent(self, client):
        """Test agent update"""
        response = client.put(
            f"/agents/{test_agent_id}",
            json={
                "name": "Updated Agent Name",
                "status": "active"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200

class TestApprovalEndpoints:
    """Test approval workflow endpoints"""
    
    def test_list_approvals(self, client):
        """Test approval listing"""
        response = client.get(
            "/approvals",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "approvals" in data

class TestDashboardEndpoints:
    """Test dashboard endpoints"""
    
    def test_dashboard_stats(self, client):
        """Test dashboard stats"""
        response = client.get(
            "/dashboard/stats",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "active_agents" in data
    
    def test_dashboard_activity(self, client):
        """Test dashboard activity"""
        response = client.get(
            "/dashboard/activity",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_analytics_overview(self, client):
        """Test analytics overview"""
        response = client.get(
            "/analytics",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200

class TestSearchEndpoints:
    """Test search endpoints"""
    
    def test_search_tasks(self, client):
        """Test task search"""
        response = client.post(
            "/search",
            json={"search_text": "test"},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

class TestCustomerServiceEndpoints:
    """Test customer service endpoints"""
    
    def test_list_sessions(self, client):
        """Test customer service sessions listing"""
        response = client.get(
            "/customer-service/sessions",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data

class TestHierarchyEndpoints:
    """Test hierarchy endpoints"""
    
    def test_get_hierarchy(self, client):
        """Test get hierarchy"""
        response = client.get(
            "/hierarchy",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "human_levels" in data
        assert "agent_levels" in data

class TestProviderConfigEndpoints:
    """Test provider config endpoints"""
    
    def test_get_provider_config(self, client):
        """Test get provider configuration"""
        response = client.get(
            "/providers/config",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
    
    def test_update_provider_config(self, client):
        """Test update provider configuration"""
        response = client.put(
            "/providers/config",
            json={
                "auth_provider": "clerk",
                "database": "supabase",
                "hosting": "vercel",
                "secrets": "env"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200

class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_enforced(self, client):
        """Test that rate limiting is enforced"""
        # Make many requests quickly
        responses = []
        for _ in range(110):  # Over the default limit
            response = client.get(
                "/dashboard/stats",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            responses.append(response.status_code)
        
        # At least some should be rate limited
        assert 429 in responses or responses[-1] == 429

class TestErrorHandling:
    """Test error responses"""
    
    def test_404_error(self, client):
        """Test 404 error response"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_validation_error(self, client):
        """Test validation error response"""
        response = client.post(
            "/tasks",
            json={},  # Missing required fields
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_unauthorized_error(self, client):
        """Test unauthorized access"""
        response = client.get("/tasks")
        
        assert response.status_code == 401

# Run with: pytest backend/tests/test_endpoints.py -v
