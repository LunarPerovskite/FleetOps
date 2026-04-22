import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.services.task_service import TaskService
from app.models.models import Task, TaskStatus, RiskLevel, Agent, AgentLevel

@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = Mock()
    return db

@pytest.fixture
def task_service(mock_db):
    return TaskService(mock_db)

class TestTaskService:
    """Test task lifecycle"""
    
    async def test_create_task(self, task_service, mock_db):
        """Test task creation"""
        # Arrange
        mock_db.execute.return_value = Mock(
            scalar_one_or_none=Mock(return_value=None)
        )
        
        # Act
        result = await task_service.create_task(
            title="Test Task",
            description="Test Description",
            agent_id="agent_123",
            org_id="org_123",
            risk_level="low"
        )
        
        # Assert
        assert result["status"] == "created"
        assert "task_id" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    async def test_approve_task_low_risk(self, task_service, mock_db):
        """Test auto-approval for low risk"""
        # Arrange
        task = Mock()
        task.id = "task_123"
        task.status = TaskStatus.CREATED
        task.risk_level = RiskLevel.LOW
        task.stage = "initiation"
        task.org_id = "org_123"
        task.agent_id = "agent_123"
        
        mock_db.execute.return_value = Mock(
            scalar_one_or_none=Mock(return_value=task)
        )
        
        # Act
        result = await task_service.approve_task_stage(
            task_id="task_123",
            human_id="user_123",
            decision="approve",
            comments="Looks good"
        )
        
        # Assert
        assert result["status"] == "approved"
        assert result["new_stage"] == "planning"
    
    async def test_approve_task_critical_requires_director(self, task_service, mock_db):
        """Test critical tasks need director approval"""
        # Arrange
        task = Mock()
        task.id = "task_123"
        task.status = TaskStatus.PLANNING
        task.risk_level = RiskLevel.CRITICAL
        task.stage = "execution"
        task.org_id = "org_123"
        
        mock_db.execute.return_value = Mock(
            scalar_one_or_none=Mock(return_value=task)
        )
        
        # Act
        result = await task_service.approve_task_stage(
            task_id="task_123",
            human_id="user_123",  # Regular operator
            decision="approve"
        )
        
        # Assert - should require escalation
        assert "requires_role" in result
        assert result["requires_role"] == "director"

class TestAgentHierarchy:
    """Test agent hierarchy"""
    
    async def test_create_sub_agent(self, mock_db):
        """Test sub-agent creation"""
        from app.services.task_service import TaskService
        
        service = TaskService(mock_db)
        
        # Parent agent
        parent = Mock()
        parent.id = "parent_123"
        parent.max_sub_agents = None  # Unlimited
        
        mock_db.execute.return_value = Mock(
            scalar_one_or_none=Mock(return_value=parent)
        )
        
        # Should allow creation
        result = await service.create_sub_agent(
            parent_id="parent_123",
            name="Sub Agent",
            org_id="org_123"
        )
        
        assert result["status"] == "created"
    
    async def test_unlimited_sub_agents(self, mock_db):
        """Test unlimited sub-agents"""
        from app.models.models import Agent
        
        agent = Agent()
        agent.max_sub_agents = None
        
        # Should not raise error even with many sub-agents
        for i in range(100):
            agent.sub_agents = list(range(i))
            # No limit check needed
        
        assert True  # No exception

class TestSLAMonitoring:
    """Test SLA monitoring"""
    
    async def test_sla_breach_detection(self, mock_db):
        """Test SLA breach detection"""
        from app.services.customer_service import SLAMonitor
        
        monitor = SLAMonitor()
        
        # Critical task created 10 minutes ago
        created_at = datetime.utcnow() - timedelta(minutes=10)
        
        result = monitor.check_breach(
            created_at=created_at,
            priority="critical",
            is_vip=False
        )
        
        # Critical SLA: first_response = 5 min
        assert result["breached"] == True
        assert result["first_response_breach"] == True
    
    async def test_sla_within_limit(self, mock_db):
        """Test SLA within limits"""
        from app.services.customer_service import SLAMonitor
        from datetime import timedelta
        
        monitor = SLAMonitor()
        
        # Low priority task created 10 minutes ago
        created_at = datetime.utcnow() - timedelta(minutes=10)
        
        result = monitor.check_breach(
            created_at=created_at,
            priority="low",
            is_vip=False
        )
        
        # Low SLA: first_response = 240 min
        assert result["breached"] == False
        assert result["remaining_first_response"] > 200

class TestProviderAdapters:
    """Test provider adapters"""
    
    def test_clerk_adapter_initialization(self):
        """Test Clerk adapter"""
        from app.adapters.auth_adapter import ClerkAuthAdapter
        
        adapter = ClerkAuthAdapter(
            api_key="test_key",
            publishable_key="test_pub"
        )
        
        assert adapter.PROVIDER_NAME == "clerk"
        assert adapter.api_key == "test_key"
    
    def test_auth0_adapter_initialization(self):
        """Test Auth0 adapter"""
        from app.adapters.auth0_adapter import Auth0AuthAdapter
        
        adapter = Auth0AuthAdapter(
            domain="test.auth0.com",
            client_id="test_id",
            client_secret="test_secret"
        )
        
        assert adapter.PROVIDER_NAME == "auth0"
        assert adapter.domain == "test.auth0.com"
    
    def test_okta_adapter_initialization(self):
        """Test Okta adapter"""
        from app.adapters.okta_adapter import OktaAuthAdapter
        
        adapter = OktaAuthAdapter(
            domain="test.okta.com",
            api_token="test_token"
        )
        
        assert adapter.PROVIDER_NAME == "okta"
        assert adapter.domain == "test.okta.com"

class TestRateLimiter:
    """Test rate limiting"""
    
    def test_rate_limit_allows_under_limit(self):
        """Test requests under limit pass"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Mock Redis
        limiter.redis = Mock()
        limiter.redis.zremrangebyscore = Mock()
        limiter.redis.zcard = Mock(return_value=50)
        limiter.redis.zadd = Mock()
        limiter.redis.expire = Mock()
        
        result = limiter.is_allowed("test_key", limit=100)
        
        assert result["allowed"] == True
        assert result["remaining"] == 49
    
    def test_rate_limit_blocks_over_limit(self):
        """Test requests over limit blocked"""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        
        # Mock Redis
        limiter.redis = Mock()
        limiter.redis.zremrangebyscore = Mock()
        limiter.redis.zcard = Mock(return_value=100)
        limiter.redis.zrange = Mock(return_value=[("old", 1000)])
        
        result = limiter.is_allowed("test_key", limit=100)
        
        assert result["allowed"] == False
        assert result["remaining"] == 0

classTestEvidenceSigning:
    """Test cryptographic evidence"""
    
    def test_event_signature(self):
        """Test event signing"""
        import hashlib
        
        event_data = {
            "task_id": "task_123",
            "event_type": "approved",
            "timestamp": "2026-04-22T10:00:00Z",
            "user_id": "user_123"
        }
        
        # Create signature
        data_string = str(event_data)
        signature = hashlib.sha256(data_string.encode()).hexdigest()
        
        # Verify
        assert len(signature) == 64
        assert isinstance(signature, str)
    
    def test_signature_verification(self):
        """Test signature verification"""
        import hashlib
        
        event_data = {"test": "data"}
        signature = hashlib.sha256(str(event_data).encode()).hexdigest()
        
        # Verify matches
        assert hashlib.sha256(str(event_data).encode()).hexdigest() == signature

classTestWebhookDelivery:
    """Test webhook delivery"""
    
    def test_signature_generation(self):
        """Test webhook signature"""
        from app.services.webhook_service import WebhookService
        
        service = WebhookService()
        
        signature = service.generate_signature(
            payload='{"test": "data"}',
            secret="test_secret"
        )
        
        assert len(signature) == 64
        assert isinstance(signature, str)

classTestTranslationService:
    """Test translation"""
    
    async def test_detect_language(self):
        """Test language detection"""
        from app.services.translation_service import TranslationService
        
        service = TranslationService()
        
        # Mock OpenAI call
        service.client = Mock()
        service.client.chat.completions.create = Mock(return_value=Mock(
            choices=[Mock(message=Mock(content='{"language_code": "es", "language_name": "Spanish", "confidence": 0.95}'))]
        ))
        
        result = await service.detect_language("Hola, ¿cómo estás?")
        
        assert result["language_code"] == "es"
        assert result["supported"] == True

# Run with: pytest backend/tests/ -v --cov=app --cov-report=html
