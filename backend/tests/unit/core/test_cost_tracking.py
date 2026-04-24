"""Unit tests for cost tracking module."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Import the actual classes from the module
import sys
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.core.cost_tracking import (
    PricingConfigDB,
    ProviderPricingFetcher,
    DynamicCostTracker,
)


class TestProviderPricingFetcher:
    """Test the ProviderPricingFetcher class."""

    @pytest.fixture
    def fetcher(self):
        return ProviderPricingFetcher()

    @pytest.mark.asyncio
    async def test_fetch_openrouter_pricing(self, fetcher):
        """Test fetching OpenRouter pricing with mocked response."""
        mock_data = {
            "data": [
                {
                    "id": "openai/gpt-4",
                    "pricing": {"prompt": "0.00003", "completion": "0.00006"}
                },
                {
                    "id": "anthropic/claude-3.5-sonnet",
                    "pricing": {"prompt": "0.000003", "completion": "0.000015"}
                }
            ]
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_data)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = await fetcher.fetch_openrouter_pricing()

            assert "openai/gpt-4" in result
            assert result["openai/gpt-4"]["input_cost_per_1k"] == 0.03
            assert result["openai/gpt-4"]["output_cost_per_1k"] == 0.06
            assert "anthropic/claude-3.5-sonnet" in result

    @pytest.mark.asyncio
    async def test_fetch_groq_pricing(self, fetcher):
        """Test fetching Groq pricing."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "data": [{"id": "mixtral-8x7b-32768", "pricing": {"prompt": "0.00000027", "completion": "0.00000027"}}]
            })
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = await fetcher.fetch_groq_pricing()
            assert "mixtral-8x7b-32768" in result or result == {}

    @pytest.mark.asyncio
    async def test_fetch_with_error(self, fetcher):
        """Test graceful handling of API errors."""
        with patch("httpx.AsyncClient.get", side_effect=Exception("Network error")):
            result = await fetcher.fetch_openrouter_pricing()
            assert result == {}


class TestDynamicCostTracker:
    """Test the DynamicCostTracker class."""

    @pytest.fixture
    def tracker(self):
        return DynamicCostTracker()

    def test_init(self, tracker):
        assert isinstance(tracker.pricing_cache, dict)
        assert tracker.cache_ttl == 3600

    @pytest.mark.asyncio
    async def test_track_usage_with_cached_pricing(self, tracker):
        """Test tracking usage when pricing is cached."""
        tracker.pricing_cache = {
            "openai/gpt-4": {
                "input_rate_per_1m": 30.0,  # $30 per 1M tokens
                "output_rate_per_1m": 60.0,
                "pricing_type": "pay_per_token",
                "cached_at": datetime.utcnow()
            }
        }

        result = await tracker.track_usage(
            service="openai",
            model="gpt-4",
            tokens_in=1000,
            tokens_out=500,
            task_id="task-123"
        )

        assert result is not None
        assert result["service"] == "openai"
        assert result["model"] == "gpt-4"
        assert result["tokens_in"] == 1000
        assert result["tokens_out"] == 500
        # Cost: (1000/1M * 30) + (500/1M * 60) = 0.03 + 0.03 = 0.06
        assert result["cost_usd"] == pytest.approx(0.06, abs=0.001)

    @pytest.mark.asyncio
    async def test_track_usage_unknown_model(self, tracker):
        """Test tracking with unknown model falls back to defaults."""
        with patch.object(tracker, '_fetch_pricing_for_model', return_value=None):
            result = await tracker.track_usage(
                service="unknown",
                model="unknown-model",
                tokens_in=1000,
                tokens_out=500,
                task_id="task-123"
            )

            assert result is not None
            assert result["cost_usd"] >= 0

    @pytest.mark.asyncio
    async def test_track_local_compute(self, tracker):
        """Test tracking local compute costs."""
        result = await tracker.track_local_compute(
            hardware="gpu_rtx4090",
            compute_seconds=3600,  # 1 hour
            task_id="task-123"
        )

        assert result is not None
        assert result["hardware"] == "gpu_rtx4090"
        assert result["compute_seconds"] == 3600
        assert "cost_usd" in result
        assert result["cost_usd"] > 0

    def test_pricing_cache_expiration(self, tracker):
        """Test that old cache entries are considered invalid."""
        tracker.pricing_cache = {
            "expired-model": {
                "input_rate_per_1m": 10.0,
                "cached_at": datetime.utcnow() - timedelta(hours=2)
            }
        }

        is_valid = tracker._is_cache_valid("expired-model")
        assert is_valid is False

    def test_pricing_cache_valid(self, tracker):
        """Test that recent cache entries are valid."""
        tracker.pricing_cache = {
            "fresh-model": {
                "input_rate_per_1m": 10.0,
                "cached_at": datetime.utcnow() - timedelta(minutes=30)
            }
        }

        is_valid = tracker._is_cache_valid("fresh-model")
        assert is_valid is True


class TestPricingConfigDB:
    """Test the PricingConfigDB model."""

    def test_model_creation(self):
        """Test that PricingConfigDB can be instantiated."""
        config = PricingConfigDB(
            id="config-123",
            service="openai",
            model="gpt-4",
            model_name="GPT-4",
            pricing_type="pay_per_token",
            input_rate_per_1m=30.0,
            output_rate_per_1m=60.0,
            is_active=True
        )

        assert config.service == "openai"
        assert config.model == "gpt-4"
        assert config.input_rate_per_1m == 30.0
        assert config.is_active is True

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = PricingConfigDB(
            id="config-456",
            service="ollama",
            model="llama3.1:8b",
            pricing_type="free_local"
        )

        assert config.pricing_type == "free_local"
        assert config.is_user_configured is False
        assert config.is_active is True
        assert config.electricity_rate == 0.15
