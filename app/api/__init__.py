"""API module initialization."""

from app.api.main import app
from app.api.deps import get_current_user, get_admin_user, get_optional_user

__all__ = ["app", "get_current_user", "get_admin_user", "get_optional_user"]