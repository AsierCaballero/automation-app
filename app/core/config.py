"""Application settings and configuration."""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite:///./automation.db"
    app_port: int = 8000
    log_level: str = "INFO"
    default_timeout: int = 300
    max_concurrent: int = 5

    secret_key: str = "change-me-in-production-use-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    allowed_hosts: str = "localhost,127.0.0.1"
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    enable_scheduling: bool = True
    scheduler_timezone: str = "UTC"

    enable_webhooks: bool = True
    webhook_timeout: int = 30

    enable_command_validation: bool = True
    allowed_commands: str = "tar,gzip,rsync,docker,pg_dump,mysqldump,curl,wget"

    default_retry_attempts: int = 3
    default_retry_delay: int = 5

    log_format: str = "json"
    log_file: str = "/app/logs/automation.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_base_dir() -> Path:
    """Get base directory of the application."""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Get data directory."""
    data_dir = get_base_dir() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """Get logs directory."""
    logs_dir = get_base_dir() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_scripts_dir() -> Path:
    """Get scripts directory."""
    scripts_dir = get_base_dir() / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    return scripts_dir


settings = get_settings()