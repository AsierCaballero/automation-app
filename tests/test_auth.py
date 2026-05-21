"""Tests for user service."""

import pytest
from app.models import User
from app.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    authenticate_user,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password("wrong_password", hashed) is False


class TestTokenService:
    """Test token service functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token(data={"sub": "testuser"})
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """Test decoding valid token."""
        token = create_access_token(data={"sub": "testuser"})
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.username == "testuser"

    def test_decode_access_token_invalid(self):
        """Test decoding invalid token."""
        token_data = decode_access_token("invalid_token")
        assert token_data is None


class TestAuthentication:
    """Test user authentication."""

    def test_authenticate_user_success(self, db_session, admin_user):
        """Test successful authentication."""
        user = authenticate_user(db_session, "admin", "testpass123")
        assert user is not None
        assert user.username == "admin"

    def test_authenticate_user_wrong_password(self, db_session, admin_user):
        """Test authentication with wrong password."""
        user = authenticate_user(db_session, "admin", "wrongpassword")
        assert user is None

    def test_authenticate_user_not_found(self, db_session):
        """Test authentication with non-existent user."""
        user = authenticate_user(db_session, "nonexistent", "password")
        assert user is None