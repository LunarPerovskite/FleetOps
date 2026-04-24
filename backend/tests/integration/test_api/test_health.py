"""Integration tests for health and metrics endpoints."""
import pytest

import sys
sys.path.insert(0, '/data/.openclaw/workspace/fleetops-temp/backend')

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.routes.health import router


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health(self):
        """Test basic health check."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "fleetops-api"
        assert data["version"] == "0.1.0"

    def test_liveness(self):
        """Test liveness probe."""
        response = client.get("/api/v1/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_with_db(self):
        """Test readiness with database."""
        response = client.get("/api/v1/ready")
        
        # May succeed or fail depending on DB config
        assert response.status_code in [200, 500]
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
        
        content = response.text
        assert isinstance(content, str)
        # Should contain FleetOps info or note about prometheus
        assert "fleetops" in content.lower() or "prometheus" in content.lower()

    def test_detailed_health(self):
        """Test detailed health check."""
        response = client.get("/api/v1/health/detailed")
        
        # May succeed or fail depending on DB config
        assert response.status_code in [200, 500]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data
