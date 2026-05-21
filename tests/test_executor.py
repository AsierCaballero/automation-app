"""Tests for task execution."""

import pytest
from app.services.executor import execute_task, ExecutionResult


class TestExecuteTask:
    """Test task execution service."""

    def test_execute_simple_command(self):
        """Test execution of simple shell command."""
        result = execute_task("echo 'Hello World'", timeout=30)
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert "Hello World" in result.output
        assert result.return_code == 0

    def test_execute_failing_command(self):
        """Test execution of failing command."""
        result = execute_task("exit 1", timeout=30)
        assert result.success is False
        assert result.return_code == 1

    def test_execute_invalid_command(self):
        """Test execution with invalid command."""
        result = execute_task("nonexistent_command_12345", timeout=30)
        assert result.success is False

    def test_execute_command_with_timeout(self):
        """Test execution with timeout."""
        result = execute_task("sleep 5", timeout=1)
        assert result.success is False
        assert "timeout" in result.error.lower() or result.error is not None

    def test_execution_result_to_dict(self):
        """Test ExecutionResult conversion to dictionary."""
        result = ExecutionResult(
            success=True,
            output="test output",
            error=None,
            return_code=0,
            duration_ms=100,
        )
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["output"] == "test output"
        assert result_dict["duration_ms"] == 100