"""Logging configuration and utilities."""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from app.core.config import settings, get_logs_dir


class JsonFormatter(logging.Formatter):
    """Format logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "task_name"):
            log_data["task_name"] = record.task_name
        return json.dumps(log_data)


def setup_logging(name: str = "automation") -> logging.Logger:
    """Set up application logging."""
    logger = logging.getLogger(name)
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    if settings.log_file:
        try:
            log_path = Path(settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            file_handler.setLevel(level)
            if settings.log_format == "json":
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(console_format)
            logger.addHandler(file_handler)
        except (OSError, PermissionError):
            pass

    return logger


def get_logger(name: str = "automation") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)