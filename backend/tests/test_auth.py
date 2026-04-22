import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db
from app.models.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user(setup_db):
    response = client.post(
        "/api/v1/auth/register",
        data={"email": "test@example.com", "password": "password123", "name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["email"] == "test@example.com"

def test_login_user(setup_db):
    # Register first
    client.post("/api/v1/auth/register", data={"email": "login@test.com", "password": "pass123", "name": "Login Test"})
    
    response = client.post(
        "/api/v1/auth/login",
        data={"email": "login@test.com", "password": "pass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(setup_db):
    response = client.post(
        "/api/v1/auth/login",
        data={"email": "wrong@test.com", "password": "wrongpass"}
    )
    assert response.status_code == 401

def test_protected_route_without_auth():
    response = client.get("/api/v1/agents/")
    assert response.status_code == 403
