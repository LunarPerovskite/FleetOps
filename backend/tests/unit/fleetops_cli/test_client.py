"""Tests for FleetOpsClient library"""
import pytest
import sys
from unittest.mock import AsyncMock, patch

# sys.path removed - using PYTHONPATH

from fleetops_cli.client import FleetOpsClient, create_client


class TestFleetOpsClient:
    """Test FleetOpsClient"""

    def test_create_client(self):
        """Test creating a client"""
        client = FleetOpsClient(api_url="http://test:8000", api_key="test-key")
        assert client.api_url == "http://test:8000"
        assert client.api_key == "test-key"

    def test_create_client_defaults(self):
        """Test client with defaults"""
        client = FleetOpsClient()
        assert client.api_url == "http://localhost:8000"
        assert client.api_key is None

    def test_create_client_convenience(self):
        """Test create_client helper"""
        client = create_client(api_url="http://test:8000")
        assert client.api_url == "http://test:8000"

    @pytest.mark.asyncio
    async def test_request_approval_success(self):
        """Test successful approval request"""
        client = FleetOpsClient()
        
        mock_response = AsyncMock()
        mock_response.json = lambda: {"status": "approved", "can_proceed": True}
        mock_response.raise_for_status = lambda: None
        
        with patch.object(client._http_client, 'post', return_value=mock_response) as mock_post:
            result = await client.request_approval(
                agent_id="test-agent",
                agent_name="Test",
                action="bash",
                arguments="ls -la"
            )
            
            assert result["can_proceed"] is True

    @pytest.mark.asyncio
    async def test_request_approval_connection_error(self):
        """Test handling connection error"""
        client = FleetOpsClient(api_url="http://invalid:8000")
        
        result = await client.request_approval(
            agent_id="test",
            agent_name="Test",
            action="bash"
        )
        
        # Should fail-safe: allow but warn
        assert result["can_proceed"] is True
        assert result["status"] == "fleetops_unavailable"

    @pytest.mark.asyncio
    async def test_approve(self):
        """Test approve method"""
        client = FleetOpsClient()
        
        mock_response = AsyncMock()
        mock_response.json = lambda: {"status": "success"}
        mock_response.raise_for_status = lambda: None
        
        with patch.object(client._http_client, 'post', return_value=mock_response) as mock_post:
            result = await client.approve("approval-123", scope="session")
            
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_reject(self):
        """Test reject method"""
        client = FleetOpsClient()
        
        mock_response = AsyncMock()
        mock_response.json = lambda: {"status": "success"}
        mock_response.raise_for_status = lambda: None
        
        with patch.object(client._http_client, 'post', return_value=mock_response) as mock_post:
            result = await client.reject("approval-123", comments="Too risky")
            
            assert result["status"] == "success"

    def test_sync_wrappers(self):
        """Test synchronous wrappers"""
        client = FleetOpsClient()
        
        with patch.object(client, 'request_approval', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"can_proceed": True}
            
            result = client.request_approval_sync(
                agent_id="test",
                agent_name="Test",
                action="bash"
            )
            
            assert result["can_proceed"] is True


class TestClientContextManager:
    """Test client context manager"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager"""
        async with FleetOpsClient() as client:
            assert client is not None

    def test_sync_context_manager(self):
        """Test sync context manager"""
        with FleetOpsClient() as client:
            assert client is not None
