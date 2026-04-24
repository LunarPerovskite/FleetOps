"""Circuit breaker pattern for FleetOps

Prevents cascading failures when external services go down.
"""

import time
import asyncio
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from functools import wraps


class CircuitState(Enum):
    CLOSED = auto()    # Normal operation
    OPEN = auto()      # Failing, reject requests
    HALF_OPEN = auto() # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    expected_exception: type = Exception


class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    _instances: Dict[str, "CircuitBreaker"] = {}
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    @classmethod
    def get(cls, name: str, config: Optional[CircuitBreakerConfig] = None) -> "CircuitBreaker":
        if name not in cls._instances:
            cls._instances[name] = cls(name, config)
        return cls._instances[name]
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Retry after {self._remaining_cooldown():.0f}s"
                    )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exception:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.half_open_max_calls:
                    self._reset()
            else:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _remaining_cooldown(self) -> float:
        if self.last_failure_time is None:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, self.config.recovery_timeout - elapsed)
    
    def _reset(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED
    
    def get_status(self) -> Dict:
        return {
            "name": self.name,
            "state": self.state.name,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "remaining_cooldown": self._remaining_cooldown() if self.is_open else 0,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 3,
    expected_exception: type = Exception
):
    """Decorator to add circuit breaker to async functions"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
        expected_exception=expected_exception
    )
    breaker = CircuitBreaker.get(name, config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        # Attach breaker for testing/status
        wrapper._circuit_breaker = breaker
        return wrapper
    return decorator


# Pre-configured breakers for common services
OPENAI_BREAKER = CircuitBreaker.get("openai", CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0
))

ANTHROPIC_BREAKER = CircuitBreaker.get("anthropic", CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0
))

OLLAMA_BREAKER = CircuitBreaker.get("ollama", CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=15.0
))

OPENROUTER_BREAKER = CircuitBreaker.get("openrouter", CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0
))
