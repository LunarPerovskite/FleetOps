"""Unit tests for circuit breaker module."""
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, Mock

import sys
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    circuit_breaker
)


class TestCircuitBreaker:
    """Test the CircuitBreaker class."""

    @pytest.fixture
    def breaker(self):
        return CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=0.1,  # Fast for testing
                half_open_max_calls=2
            )
        )

    @pytest.mark.asyncio
    async def test_successful_call(self, breaker):
        """Test normal successful call."""
        mock_func = AsyncMock(return_value="success")
        
        result = await breaker.call(mock_func)
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_tracking(self, breaker):
        """Test failures are tracked."""
        mock_func = AsyncMock(side_effect=Exception("fail"))
        
        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(mock_func)
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_open_circuit_rejects(self, breaker):
        """Test open circuit rejects calls immediately."""
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = time.time()  # Current time
        
        mock_func = AsyncMock(return_value="success")
        
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(mock_func)
        
        # Should not have called the function
        mock_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_half_open_recovery(self, breaker):
        """Test circuit transitions to half-open then closed."""
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = asyncio.get_event_loop().time() - 0.2  # Past recovery timeout
        
        mock_func = AsyncMock(return_value="success")
        
        # First call after recovery - should work
        result = await breaker.call(mock_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN
        
        # Need more successes to close
        await breaker.call(mock_func)
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self, breaker):
        """Test half-open failure reopens the circuit."""
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = asyncio.get_event_loop().time() - 0.2
        
        mock_func = AsyncMock(side_effect=Exception("fail"))
        
        with pytest.raises(Exception):
            await breaker.call(mock_func)
        
        assert breaker.state == CircuitState.OPEN

    def test_get_status(self, breaker):
        """Test status reporting."""
        breaker.state = CircuitState.OPEN
        breaker.failure_count = 5
        breaker.last_failure_time = time.time()  # Failure just happened
        
        status = breaker.get_status()
        
        assert status["name"] == "test"
        assert status["state"] == "OPEN"
        assert status["failure_count"] == 5
        assert status["remaining_cooldown"] > 0

    @pytest.mark.asyncio
    async def test_singleton_instances(self):
        """Test that get() returns same instance."""
        b1 = CircuitBreaker.get("singleton_test")
        b2 = CircuitBreaker.get("singleton_test")
        
        assert b1 is b2


class TestCircuitBreakerDecorator:
    """Test the circuit_breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator on successful function."""
        @circuit_breaker("test_decorator", failure_threshold=3, recovery_timeout=1)
        async def my_function():
            return "hello"
        
        result = await my_function()
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_decorator_failure(self):
        """Test decorator tracks failures."""
        call_count = 0
        
        @circuit_breaker("test_fail", failure_threshold=2, recovery_timeout=1)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")
        
        # Should fail normally until threshold
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_function()
        
        # Circuit should be open now
        with pytest.raises(CircuitBreakerOpenError):
            await failing_function()
        
        assert call_count == 2  # Not called when open

    def test_preconfigured_breakers(self):
        """Test pre-configured breakers exist."""
        from app.core.circuit_breaker import OPENAI_BREAKER, ANTHROPIC_BREAKER, OLLAMA_BREAKER
        
        assert OPENAI_BREAKER.name == "openai"
        assert ANTHROPIC_BREAKER.name == "anthropic"
        assert OLLAMA_BREAKER.name == "ollama"


class TestCircuitBreakerConfig:
    """Test configuration."""

    def test_default_config(self):
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 30.0
        assert config.half_open_max_calls == 3

    def test_custom_config(self):
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=60.0,
            expected_exception=ValueError
        )
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 60.0
        assert config.expected_exception == ValueError
