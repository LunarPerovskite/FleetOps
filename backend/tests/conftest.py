"""Pytest fixtures for FleetOps

Shared test fixtures across all test files
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Mock database session
@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = Mock()
    db.refresh = Mock()
    return db

# Mock Redis
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = Mock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    redis.keys = AsyncMock(return_value=[])
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    return redis

# Test data fixtures
@pytest.fixture
def test_org():
    """Test organization data"""
    return {
        "id": f"org_{uuid.uuid4().hex[:8]}",
        "name": "Test Organization",
        "tier": "free",
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_user(test_org):
    """Test user data"""
    return {
        "id": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "name": "Test User",
        "role": "operator",
        "org_id": test_org["id"],
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_task(test_org):
    """Test task data"""
    return {
        "id": f"task_{uuid.uuid4().hex[:8]}",
        "title": "Test Task",
        "description": "Test Description",
        "status": "created",
        "risk_level": "low",
        "stage": "initiation",
        "agent_id": "agent_test",
        "org_id": test_org["id"],
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def test_agent(test_org):
    """Test agent data"""
    return {
        "id": f"agent_{uuid.uuid4().hex[:8]}",
        "name": "Test Agent",
        "provider": "claude",
        "model": "claude-3-sonnet",
        "level": "junior",
        "capabilities": ["coding", "analysis"],
        "org_id": test_org["id"],
        "status": "active"
    }
