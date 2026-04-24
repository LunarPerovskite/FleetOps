"""Metrics and observability for FleetOps

Exposes Prometheus-compatible metrics at /metrics endpoint.
"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

# Prometheus client (if available)
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class MetricsCollector:
    """Collect and expose application metrics"""
    
    def __init__(self):
        self._counters: Dict[str, Any] = {}
        self._histograms: Dict[str, Any] = {}
        self._gauges: Dict[str, Any] = {}
        
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus()
    
    def _init_prometheus(self):
        """Initialize Prometheus metrics"""
        # Request metrics
        self._counters["http_requests_total"] = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )
        
        self._histograms["http_request_duration_seconds"] = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # LLM Provider metrics
        self._counters["llm_requests_total"] = Counter(
            "llm_requests_total",
            "Total LLM requests",
            ["provider", "model", "status"]
        )
        
        self._histograms["llm_request_duration_seconds"] = Histogram(
            "llm_request_duration_seconds",
            "LLM request duration",
            ["provider", "model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self._counters["llm_tokens_total"] = Counter(
            "llm_tokens_total",
            "Total tokens used",
            ["provider", "model", "type"]
        )
        
        self._counters["llm_cost_usd_total"] = Counter(
            "llm_cost_usd_total",
            "Total LLM cost in USD",
            ["provider", "model"]
        )
        
        # Cost tracking
        self._gauges["total_cost_usd"] = Gauge(
            "fleetops_total_cost_usd",
            "Total cost across all tasks",
            ["org_id"]
        )
        
        self._gauges["task_cost_usd"] = Gauge(
            "fleetops_task_cost_usd",
            "Cost per task",
            ["task_id", "provider"]
        )
        
        # Agent metrics
        self._gauges["active_agents"] = Gauge(
            "fleetops_active_agents",
            "Number of active agents",
            ["org_id", "level"]
        )
        
        self._counters["agent_tasks_total"] = Counter(
            "agent_tasks_total",
            "Total tasks by agent",
            ["agent_id", "status"]
        )
        
        # Approval metrics
        self._counters["approvals_total"] = Counter(
            "approvals_total",
            "Total approval requests",
            ["stage", "status"]
        )
        
        self._histograms["approval_duration_seconds"] = Histogram(
            "approval_duration_seconds",
            "Time to resolve approvals",
            ["stage"],
            buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
        )
        
        # Circuit breaker metrics
        self._gauges["circuit_breaker_state"] = Gauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half-open, 2=open)",
            ["service"]
        )
        
        self._counters["circuit_breaker_trips_total"] = Counter(
            "circuit_breaker_trips_total",
            "Total circuit breaker trips",
            ["service"]
        )
        
        # System info
        self._info = Info("fleetops", "FleetOps information")
        self._info.info({"version": "0.1.0"})
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record an HTTP request"""
        if PROMETHEUS_AVAILABLE:
            self._counters["http_requests_total"].labels(
                method=method, endpoint=endpoint, status=str(status)
            ).inc()
            
            self._histograms["http_request_duration_seconds"].labels(
                method=method, endpoint=endpoint
            ).observe(duration)
    
    def record_llm_request(self, provider: str, model: str, status: str, duration: float):
        """Record an LLM request"""
        if PROMETHEUS_AVAILABLE:
            self._counters["llm_requests_total"].labels(
                provider=provider, model=model, status=status
            ).inc()
            
            self._histograms["llm_request_duration_seconds"].labels(
                provider=provider, model=model
            ).observe(duration)
    
    def record_tokens(self, provider: str, model: str, tokens_in: int, tokens_out: int):
        """Record token usage"""
        if PROMETHEUS_AVAILABLE:
            self._counters["llm_tokens_total"].labels(
                provider=provider, model=model, type="input"
            ).inc(tokens_in)
            
            self._counters["llm_tokens_total"].labels(
                provider=provider, model=model, type="output"
            ).inc(tokens_out)
    
    def record_cost(self, provider: str, model: str, cost_usd: float):
        """Record cost"""
        if PROMETHEUS_AVAILABLE:
            self._counters["llm_cost_usd_total"].labels(
                provider=provider, model=model
            ).inc(cost_usd)
    
    def record_approval(self, stage: str, status: str, duration: Optional[float] = None):
        """Record approval event"""
        if PROMETHEUS_AVAILABLE:
            self._counters["approvals_total"].labels(
                stage=stage, status=status
            ).inc()
            
            if duration:
                self._histograms["approval_duration_seconds"].labels(
                    stage=stage
                ).observe(duration)
    
    def set_circuit_breaker_state(self, service: str, state: int):
        """Set circuit breaker state (0=closed, 1=half-open, 2=open)"""
        if PROMETHEUS_AVAILABLE:
            self._gauges["circuit_breaker_state"].labels(
                service=service
            ).set(state)
    
    def record_circuit_breaker_trip(self, service: str):
        """Record circuit breaker trip"""
        if PROMETHEUS_AVAILABLE:
            self._counters["circuit_breaker_trips_total"].labels(
                service=service
            ).inc()
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest().decode("utf-8")
        return "# Prometheus client not installed\n"
    
    @contextmanager
    def time_request(self, method: str, endpoint: str):
        """Context manager to time requests"""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            # Status will be updated by middleware
            self._last_request = {
                "method": method,
                "endpoint": endpoint,
                "duration": duration
            }


# Global metrics collector
metrics = MetricsCollector()


def timed(provider: str = "", model: str = ""):
    """Decorator to time LLM requests and record metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start
                # Extract provider/model from kwargs or args
                p = provider or kwargs.get("provider", "unknown")
                m = model or kwargs.get("model", "unknown")
                metrics.record_llm_request(p, m, status, duration)
        return wrapper
    return decorator


def record_http_metrics(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    metrics.record_http_request(method, endpoint, status, duration)


def get_metrics_text() -> str:
    """Get metrics in Prometheus text format"""
    return metrics.get_metrics()
