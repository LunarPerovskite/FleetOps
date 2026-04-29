"""Tests for AutoDiscoveryService"""

import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.auto_discovery_service import AutoDiscoveryService


@pytest.fixture
def discovery_service():
    return AutoDiscoveryService()


@pytest.fixture
def mock_model_response():
    return [
        {
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "capabilities": ["chat", "vision"],
            "context_length": 128000,
            "pricing": {"input": 2.50, "output": 10.00},
        },
        {
            "id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
            "capabilities": ["chat", "vision"],
            "context_length": 128000,
            "pricing": {"input": 0.15, "output": 0.60},
        },
    ]


class TestAutoDiscoveryService:
    """Test suite for auto-discovery with connectors"""

    @pytest.mark.asyncio
    async def test_discover_provider_with_key(self, discovery_service, mock_model_response):
        """Should discover models when API key is available"""
        
        mock_connector = MagicMock()
        mock_connector.list_models = AsyncMock(return_value=mock_model_response)
        mock_connector.close = AsyncMock()
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            with patch.object(discovery_service, "ADAPTER_MAP", {"openai": lambda api_key=None: mock_connector}):
                models = await discovery_service.discover_provider("openai")
        
        assert len(models) == 2
        assert models[0]["id"] == "openai/gpt-4o"
        mock_connector.list_models.assert_called_once()
        mock_connector.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_provider_without_key(self, discovery_service):
        """Should skip discovery when no API key is set"""
        
        with patch.dict(os.environ, {}, clear=True):
            models = await discovery_service.discover_provider("openai")
        
        assert len(models) == 0

    @pytest.mark.asyncio
    async def test_discover_provider_with_explicit_key(self, discovery_service, mock_model_response):
        """Should use explicit API key over env var"""
        
        mock_connector = MagicMock()
        mock_connector.list_models = AsyncMock(return_value=mock_model_response)
        mock_connector.close = AsyncMock()
        
        with patch.object(discovery_service, "ADAPTER_MAP", {"openai": lambda api_key=None: mock_connector}):
            models = await discovery_service.discover_provider("openai", api_key="sk-explicit")
        
        assert len(models) == 2

    @pytest.mark.asyncio
    async def test_discover_all_configured(self, discovery_service, mock_model_response):
        """Should discover from all providers with keys"""
        
        mock_openai = MagicMock()
        mock_openai.list_models = AsyncMock(return_value=mock_model_response)
        mock_openai.close = AsyncMock()
        
        mock_anthropic = MagicMock()
        mock_anthropic.list_models = AsyncMock(return_value=[{
            "id": "anthropic/claude-3-5-sonnet",
            "name": "Claude 3.5 Sonnet",
            "capabilities": ["chat"],
            "context_length": 200000,
            "pricing": {"input": 3.00, "output": 15.00},
        }])
        mock_anthropic.close = AsyncMock()
        
        env = {
            "OPENAI_API_KEY": "sk-openai",
            "ANTHROPIC_API_KEY": "sk-anthropic",
        }
        
        adapters = {
            "openai": lambda api_key=None: mock_openai,
            "anthropic": lambda api_key=None: mock_anthropic,
        }
        
        with patch.dict(os.environ, env, clear=True):
            with patch.object(discovery_service, "ADAPTER_MAP", adapters):
                with patch("app.core.auto_discovery_service.model_registry") as mock_registry:
                    mock_registry._models = {}
                    results = await discovery_service.discover_all_configured()
        
        assert "openai" in results
        assert "anthropic" in results
        assert len(results["openai"]) == 2
        assert len(results["anthropic"]) == 1
        assert "gemini" not in results  # No key configured, skipped

    def test_normalize_model(self, discovery_service):
        """Should normalize connector output to discovery format"""
        
        raw = {
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "capabilities": ["chat", "vision"],
            "context_length": 128000,
            "pricing": {"input": 2.50, "output": 10.00},
            "provider_model_id": "gpt-4o",
        }
        
        normalized = discovery_service._normalize_model(raw, "openai")
        
        assert normalized["id"] == "openai/gpt-4o"
        assert normalized["provider"] == "openai"
        assert normalized["provider_model_id"] == "gpt-4o"
        assert normalized["type"] == "chat"
        assert normalized["pricing"]["input"] == 2.50

    @pytest.mark.asyncio
    async def test_refresh_on_key_update(self, discovery_service, mock_model_response):
        """Should discover and return models when key is updated"""
        
        mock_connector = MagicMock()
        mock_connector.list_models = AsyncMock(return_value=mock_model_response)
        mock_connector.close = AsyncMock()
        
        with patch.object(discovery_service, "ADAPTER_MAP", {"openai": lambda api_key=None: mock_connector}):
            result = await discovery_service.refresh_on_key_update("openai", "sk-new-key")
        
        assert result["provider"] == "openai"
        assert result["models_discovered"] == 2
        assert len(result["models"]) == 2
        assert result["models"][0]["id"] == "openai/gpt-4o"

    def test_get_provider_status_no_keys(self, discovery_service):
        """Should report no keys when env vars are empty"""
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.core.auto_discovery_service.model_registry") as mock_registry:
                mock_registry._models = {}
                status = discovery_service.get_provider_status()
        
        openai_status = next(s for s in status if s["provider"] == "openai")
        assert openai_status["has_api_key"] is False
        assert openai_status["models_registered"] == 0

    def test_get_provider_status_with_keys(self, discovery_service):
        """Should report keys present when env vars are set"""
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            with patch("app.core.auto_discovery_service.model_registry") as mock_registry:
                mock_registry._models = {}
                status = discovery_service.get_provider_status()
        
        openai_status = next(s for s in status if s["provider"] == "openai")
        assert openai_status["has_api_key"] is True

    @pytest.mark.asyncio
    async def test_discover_unknown_provider(self, discovery_service):
        """Should handle unknown providers gracefully"""
        
        models = await discovery_service.discover_provider("unknown_provider")
        assert len(models) == 0

    @pytest.mark.asyncio
    async def test_discover_provider_error_handling(self, discovery_service):
        """Should handle connector errors gracefully"""
        
        mock_connector = MagicMock()
        mock_connector.list_models = AsyncMock(side_effect=Exception("Connection failed"))
        mock_connector.close = AsyncMock()
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch.object(discovery_service, "ADAPTER_MAP", {"openai": lambda api_key=None: mock_connector}):
                models = await discovery_service.discover_provider("openai")
        
        assert len(models) == 0
        mock_connector.close.assert_called_once()

    def test_normalize_model_without_cost(self, discovery_service):
        """Should handle models without pricing info"""
        
        raw = {
            "id": "openai/custom-model",
            "name": "Custom Model",
        }
        
        normalized = discovery_service._normalize_model(raw, "openai")
        
        assert normalized["pricing"]["input"] == 0
        assert normalized["pricing"]["output"] == 0
        assert normalized["context_length"] == 128000  # default

    def test_normalize_model_without_slash(self, discovery_service):
        """Should handle model IDs without provider prefix"""
        
        raw = {
            "id": "gpt-4o",
            "name": "GPT-4o",
        }
        
        normalized = discovery_service._normalize_model(raw, "openai")
        
        assert normalized["id"] == "openai/gpt-4o"
        assert normalized["provider_model_id"] == "gpt-4o"
