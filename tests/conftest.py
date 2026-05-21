"""Test configuration and fixtures."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import User, Task, Tag, ExecutionLog, Schedule, Webhook


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def admin_user(db_session):
    """Create admin user for testing."""
    from app.services.auth import get_password_hash
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpass123"),
        is_superuser=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    """Create regular user for testing."""
    from app.services.auth import get_password_hash
    user = User(
        username="testuser",
        email="user@test.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_task(db_session):
    """Create sample task for testing."""
    task = Task(
        name="test-task",
        description="Test task description",
        command="echo 'Hello World'",
        task_type="shell",
        timeout=60,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def sample_tag(db_session):
    """Create sample tag for testing."""
    tag = Tag(name="test-tag", color="#ff0000")
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)
    return tag


@pytest.fixture
def sample_execution_log(db_session, sample_task):
    """Create sample execution log for testing."""
    log = ExecutionLog(
        task_id=sample_task.id,
        task_name=sample_task.name,
        status="success",
        output="Hello World",
        return_code=0,
        duration_ms=100,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        trigger_type="manual",
        triggered_by="test_user",
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log


@pytest.fixture
def sample_webhook(db_session):
    """Create sample webhook for testing."""
    webhook = Webhook(
        name="test-webhook",
        url="https://example.com/webhook",
        events=["task.success", "task.failed"],
        enabled=True,
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    return webhook


@pytest.fixture
def sample_schedule(db_session, sample_task):
    """Create sample schedule for testing."""
    schedule = Schedule(
        task_id=sample_task.id,
        cron_expression="0 * * * *",
        enabled=True,
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    return schedule


@pytest.fixture
def auth_token(admin_user):
    """Generate auth token for testing."""
    from app.services.auth import create_access_token
    return create_access_token(data={"sub": admin_user.username})


@pytest.fixture
def user_token(regular_user):
    """Generate auth token for regular user."""
    from app.services.auth import create_access_token
    return create_access_token(data={"sub": regular_user.username})