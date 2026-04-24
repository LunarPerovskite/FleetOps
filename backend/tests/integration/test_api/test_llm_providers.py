"""Integration tests for LLM Provider API routes."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

import sys
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.llm_providers import router


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


class TestLLMProviderRoutes:
    """Test LLM provider API routes."""

    def test_list_providers(self):
        """Test listing all providers."""
        response = client.get("/api/v1/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have entries for each provider
        provider_names = [p["provider"] for p in data]
        assert "openai" in provider_names
        assert "anthropic" in provider_names

    def test_list_provider_models_not_found(self):
        """Test listing models for non-existent provider."""
        response = client.get("/api/v1/providers/nonexistent/models")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.adapters.llm_providers.OpenAIAdapter")
    def test_chat_openai_success(self, mock_adapter_class):
        """Test successful OpenAI chat."""
        mock_adapter = Mock()
        mock_adapter.chat = AsyncMock(return_value={
            "status": "success",
            "content": "Hello!",
            "model": "gpt-4",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "cost_usd": "0.03",
            "pricing_source": "api_fetched"
        })
        mock_adapter.close = AsyncMock()
        mock_adapter_class.return_value = mock_adapter
        
        # Mock auth
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/openai",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "task_id": "task-123",
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["content"] == "Hello!"
        assert data["cost_usd"] == "0.03"
        
        mock_adapter.chat.assert_called_once()
        mock_adapter.close.assert_called_once()

    @patch("app.adapters.llm_providers.AnthropicAdapter")
    def test_chat_anthropic_error(self, mock_adapter_class):
        """Test Anthropic chat with error."""
        mock_adapter = Mock()
        mock_adapter.chat = AsyncMock(side_effect=Exception("API Error"))
        mock_adapter.close = AsyncMock()
        mock_adapter_class.return_value = mock_adapter
        
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/anthropic",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "task_id": "task-123",
                    "max_tokens": 100
                }
            )
        
        assert response.status_code == 502
        mock_adapter.close.assert_called_once()

    @patch("app.adapters.llm_providers.GeminiAdapter")
    def test_chat_gemini(self, mock_adapter_class):
        """Test Gemini chat."""
        mock_adapter = Mock()
        mock_adapter.chat = AsyncMock(return_value={
            "status": "success",
            "content": "Hi there!",
            "model": "gemini-1.5-pro",
            "usage": {"input_tokens": 5, "output_tokens": 3},
            "cost_usd": "0.00",
            "pricing_source": "api_fetched"
        })
        mock_adapter.close = AsyncMock()
        mock_adapter_class.return_value = mock_adapter
        
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/gemini",
                json={
                    "messages": [{"role": "user", "content": "Hi"}],
                    "task_id": "task-123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hi there!"

    @patch("app.adapters.llm_providers.AzureOpenAIAdapter")
    def test_chat_azure(self, mock_adapter_class):
        """Test Azure OpenAI chat."""
        mock_adapter = Mock()
        mock_adapter.chat = AsyncMock(return_value={
            "status": "success",
            "content": "Azure response",
            "model": "gpt-4",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "cost_usd": "0.03",
            "pricing_source": "api_fetched"
        })
        mock_adapter.close = AsyncMock()
        mock_adapter_class.return_value = mock_adapter
        
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/azure?deployment=my-deployment",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "task_id": "task-123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Azure response"

    @patch("app.adapters.llm_providers.UnifiedLLMChatAdapter")
    def test_chat_unified(self, mock_adapter_class):
        """Test unified chat with auto-routing."""
        mock_adapter = Mock()
        mock_adapter.chat = AsyncMock(return_value={
            "status": "success",
            "content": "Routed response",
            "model": "gpt-4",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "cost_usd": "0.03",
            "pricing_source": "api_fetched"
        })
        mock_adapter.close = AsyncMock()
        mock_adapter_class.return_value = mock_adapter
        
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat?strategy=cost",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "task_id": "task-123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Routed response"


class TestChatRequestValidation:
    """Test request validation."""

    def test_missing_messages(self):
        """Test request without messages fails."""
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/openai",
                json={
                    "task_id": "task-123"
                }
            )
        
        assert response.status_code == 422

    def test_missing_task_id(self):
        """Test request without task_id fails."""
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/openai",
                json={
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
        
        assert response.status_code == 422

    def test_invalid_temperature(self):
        """Test temperature out of range fails."""
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/openai",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "task_id": "task-123",
                    "temperature": 3.0  # > 2.0
                }
            )
        
        assert response.status_code == 422

    def test_invalid_max_tokens(self):
        """Test max_tokens out of range fails."""
        with patch("app.api.routes.llm_providers.verify_token", return_value={"id": "user1"}):
            response = client.post(
                "/api/v1/chat/openai",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "task_id": "task-123",
                    "max_tokens": 0  # < 1
                }
            )
        
        assert response.status_code == 422
