import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_auth import client, setup_db

def test_create_task(setup_db):
    # Register and login
    client.post("/api/v1/auth/register", data={"email": "task@test.com", "password": "pass123", "name": "Task Test"})
    login = client.post("/api/v1/auth/login", data={"email": "task@test.com", "password": "pass123"})
    token = login.json()["access_token"]
    
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Test Task", "description": "Test description", "risk_level": "low"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "created"

def test_list_tasks(setup_db):
    client.post("/api/v1/auth/register", data={"email": "list@test.com", "password": "pass123", "name": "List Test"})
    login = client.post("/api/v1/auth/login", data={"email": "list@test.com", "password": "pass123"})
    token = login.json()["access_token"]
    
    # Create task
    client.post("/api/v1/tasks/", json={"title": "Task 1", "risk_level": "low"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/api/v1/tasks/", json={"title": "Task 2", "risk_level": "medium"}, headers={"Authorization": f"Bearer {token}"})
    
    response = client.get("/api/v1/tasks/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_task_lifecycle(setup_db):
    client.post("/api/v1/auth/register", data={"email": "lifecycle@test.com", "password": "pass123", "name": "Lifecycle Test"})
    login = client.post("/api/v1/auth/login", data={"email": "lifecycle@test.com", "password": "pass123"})
    token = login.json()["access_token"]
    
    # Create
    task = client.post("/api/v1/tasks/", json={"title": "Lifecycle Task", "risk_level": "medium"}, headers={"Authorization": f"Bearer {token}"})
    task_id = task.json()["id"]
    
    # Approve initiation → planning
    response = client.post(f"/api/v1/tasks/{task_id}/approve", json={"decision": "approve", "comments": "Looks good"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["new_stage"] == "planning"
    
    # Approve planning → execution
    response = client.post(f"/api/v1/tasks/{task_id}/approve", json={"decision": "approve"}, headers={"Authorization": f"Bearer {token}"})
    assert response.json()["new_stage"] == "execution"
    
    # Approve execution → review
    response = client.post(f"/api/v1/tasks/{task_id}/approve", json={"decision": "approve"}, headers={"Authorization": f"Bearer {token}"})
    assert response.json()["new_stage"] == "review"
    
    # Approve review → external_action
    response = client.post(f"/api/v1/tasks/{task_id}/approve", json={"decision": "approve"}, headers={"Authorization": f"Bearer {token}"})
    assert response.json()["new_stage"] == "external_action"
    
    # Approve external_action → delivery (completed)
    response = client.post(f"/api/v1/tasks/{task_id}/approve", json={"decision": "approve"}, headers={"Authorization": f"Bearer {token}"})
    assert response.json()["new_stage"] == "delivery"
    
    # Verify task is completed
    task = client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert task.json()["status"] == "completed"
