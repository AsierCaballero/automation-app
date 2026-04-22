"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.database import get_db
from app.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for tests."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client."""
    Base.metadata.create_all(bind=test_engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    from app.services.auth import get_password_hash
    user = User(
        username="testadmin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpass123"),
        is_superuser=True,
        is_active=True,
    )
    db = TestSessionLocal()
    db.add(user)
    db.commit()

    response = client.post("/auth/login", json={
        "username": "testadmin",
        "password": "testpass123",
    })
    token = response.json()["access_token"]
    db.close()
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns correct status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, client):
        """Test successful login."""
        from app.services.auth import get_password_hash
        user = User(
            username="logintest",
            email="login@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db = TestSessionLocal()
        db.add(user)
        db.commit()
        db.close()

        response = client.post("/auth/login", json={
            "username": "logintest",
            "password": "password123",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"


class TestTaskEndpoints:
    """Test task management endpoints."""

    def test_list_tasks(self, client, auth_headers):
        """Test listing tasks."""
        response = client.get("/tasks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client, auth_headers):
        """Test task creation."""
        response = client.post("/tasks", headers=auth_headers, json={
            "name": "test-task",
            "command": "echo 'test'",
            "description": "Test task",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-task"

    def test_create_task_duplicate(self, client, auth_headers):
        """Test creating duplicate task."""
        client.post("/tasks", headers=auth_headers, json={
            "name": "duplicate-task",
            "command": "echo 'test'",
        })
        response = client.post("/tasks", headers=auth_headers, json={
            "name": "duplicate-task",
            "command": "echo 'test'",
        })
        assert response.status_code == 400

    def test_get_task(self, client, auth_headers):
        """Test getting single task."""
        client.post("/tasks", headers=auth_headers, json={
            "name": "get-task",
            "command": "echo 'test'",
        })
        response = client.get("/tasks/get-task", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "get-task"

    def test_get_task_not_found(self, client, auth_headers):
        """Test getting non-existent task."""
        response = client.get("/tasks/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_task(self, client, auth_headers):
        """Test deleting task."""
        client.post("/tasks", headers=auth_headers, json={
            "name": "delete-task",
            "command": "echo 'test'",
        })
        response = client.delete("/tasks/delete-task", headers=auth_headers)
        assert response.status_code == 204

    def test_run_task(self, client, auth_headers):
        """Test running task."""
        client.post("/tasks", headers=auth_headers, json={
            "name": "run-task",
            "command": "echo 'Hello'",
        })
        response = client.post("/tasks/run-task/run", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestScheduleEndpoints:
    """Test schedule management endpoints."""

    def test_list_schedules(self, client, auth_headers):
        """Test listing schedules."""
        response = client.get("/schedules", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestWebhookEndpoints:
    """Test webhook management endpoints."""

    def test_list_webhooks(self, client, auth_headers):
        """Test listing webhooks."""
        response = client.get("/webhooks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_webhook(self, client, auth_headers):
        """Test webhook creation."""
        response = client.post("/webhooks", headers=auth_headers, json={
            "name": "test-webhook",
            "url": "https://example.com/hook",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-webhook"