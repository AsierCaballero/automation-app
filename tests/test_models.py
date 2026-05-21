"""Tests for models."""

import pytest
from datetime import datetime
from app.models import User, Task, Tag, ExecutionLog, Schedule, Webhook


class TestUserModel:
    """Test User model."""

    def test_create_user(self, db_session):
        """Test user creation."""
        from app.services.auth import get_password_hash
        user = User(
            username="newuser",
            email="new@test.com",
            hashed_password=get_password_hash("password"),
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "newuser"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_user_repr(self, admin_user):
        """Test user string representation."""
        assert "admin" in repr(admin_user)


class TestTaskModel:
    """Test Task model."""

    def test_create_task(self, db_session):
        """Test task creation."""
        task = Task(
            name="new-task",
            command="echo 'test'",
            description="Test task",
        )
        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert task.name == "new-task"
        assert task.status == "idle"
        assert task.active is True

    def test_task_repr(self, sample_task):
        """Test task string representation."""
        assert "test-task" in repr(sample_task)

    def test_task_with_tags(self, db_session, sample_task, sample_tag):
        """Test task with tags."""
        sample_task.tags.append(sample_tag)
        db_session.commit()

        assert len(sample_task.tags) == 1
        assert sample_task.tags[0].name == "test-tag"


class TestTagModel:
    """Test Tag model."""

    def test_create_tag(self, db_session):
        """Test tag creation."""
        tag = Tag(name="new-tag", color="#00ff00")
        db_session.add(tag)
        db_session.commit()

        assert tag.id is not None
        assert tag.name == "new-tag"
        assert tag.color == "#00ff00"


class TestExecutionLogModel:
    """Test ExecutionLog model."""

    def test_create_execution_log(self, db_session, sample_task):
        """Test execution log creation."""
        log = ExecutionLog(
            task_id=sample_task.id,
            task_name=sample_task.name,
            status="success",
            output="test output",
            return_code=0,
            duration_ms=100,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )
        db_session.add(log)
        db_session.commit()

        assert log.id is not None
        assert log.task_name == sample_task.name
        assert log.status == "success"

    def test_execution_log_repr(self, sample_execution_log):
        """Test execution log string representation."""
        assert "test-task" in repr(sample_execution_log)


class TestScheduleModel:
    """Test Schedule model."""

    def test_create_schedule(self, db_session, sample_task):
        """Test schedule creation."""
        schedule = Schedule(
            task_id=sample_task.id,
            cron_expression="0 * * * *",
        )
        db_session.add(schedule)
        db_session.commit()

        assert schedule.id is not None
        assert schedule.cron_expression == "0 * * * *"
        assert schedule.enabled is True


class TestWebhookModel:
    """Test Webhook model."""

    def test_create_webhook(self, db_session):
        """Test webhook creation."""
        webhook = Webhook(
            name="test-webhook",
            url="https://example.com/hook",
            events=["task.success"],
        )
        db_session.add(webhook)
        db_session.commit()

        assert webhook.id is not None
        assert webhook.name == "test-webhook"
        assert webhook.enabled is True

    def test_webhook_repr(self, sample_webhook):
        """Test webhook string representation."""
        assert "test-webhook" in repr(sample_webhook)