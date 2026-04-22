"""Tests for command validation."""

import pytest
from app.services.command_validator import CommandValidator, command_validator


class TestCommandValidator:
    """Test command validation service."""

    def test_validate_safe_command(self):
        """Test validation of safe commands."""
        is_valid, error = command_validator.validate("tar -czf backup.tar.gz ./data")
        assert is_valid is True
        assert error is None

    def test_validate_empty_command(self):
        """Test validation of empty command."""
        is_valid, error = command_validator.validate("")
        assert is_valid is False
        assert error is not None

    def test_validate_dangerous_pattern_rm_rf(self):
        """Test detection of dangerous rm -rf pattern."""
        is_valid, error = command_validator.validate("rm -rf /")
        assert is_valid is False
        assert "forbidden pattern" in error.lower()

    def test_validate_dangerous_pattern_eval(self):
        """Test detection of eval pattern."""
        is_valid, error = command_validator.validate("eval $(malicious command)")
        assert is_valid is False
        assert "forbidden pattern" in error.lower()

    def test_validate_dangerous_sudo(self):
        """Test detection of sudo command."""
        is_valid, error = command_validator.validate("sudo rm -rf /")
        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_sanitize_command(self):
        """Test command sanitization."""
        sanitized = command_validator.sanitize("rm -rf /")
        assert "[REMOVED]" in sanitized


class TestCommandValidatorInstance:
    """Test CommandValidator class."""

    def test_custom_allowed_commands(self):
        """Test validation with custom allowed commands."""
        validator = CommandValidator()
        validator.allowed_commands = ["tar", "gzip"]

        is_valid, error = validator.validate("tar -czf backup.tar.gz ./data")
        assert is_valid is True

        is_valid, error = validator.validate("curl http://example.com")
        assert is_valid is False