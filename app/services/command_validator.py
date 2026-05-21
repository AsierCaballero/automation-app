"""Command validation service for security."""

import re
from typing import List, Optional, Tuple
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("security")


class CommandValidator:
    """Validate commands for security."""

    FORBIDDEN_PATTERNS = [
        r"rm\s+-rf\s+/",
        r":\(\)\{",
        r"curl\s+\|sh",
        r"wget\s+\|sh",
        r";\s*rm\s+",
        r"&\s*rm\s+",
        r"\|\s*rm\s+",
        r"eval\s+",
        r"exec\s+",
        r"chmod\s+-R\s+777",
        r"chown\s+-R",
        r">\s*/etc/passwd",
        r">\s*/etc/shadow",
        r"mv\s+/dev/null",
        r"cat\s+/dev/urandom",
        r"fork\s+",
        r"while\s+true",
        r"nohup\s+",
    ]

    DANGEROUS_COMMANDS = [
        "sudo",
        "su",
        "passwd",
        "shutdown",
        "reboot",
        "halt",
        "init",
        "systemctl",
        "service",
        "chroot",
        "mount",
        "umount",
        "fdisk",
        "mkfs",
        "dd",
    ]

    def __init__(self) -> None:
        self.allowed_commands = (
            settings.allowed_commands.split(",") if settings.enable_command_validation else []
        )
        self.forbidden_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.FORBIDDEN_PATTERNS
        ]

    def validate(self, command: str) -> Tuple[bool, Optional[str]]:
        """Validate a command. Returns (is_valid, error_message)."""
        if not command or not command.strip():
            return False, "Command cannot be empty"

        if settings.enable_command_validation and self.allowed_commands:
            first_word = command.strip().split()[0]
            if first_word not in self.allowed_commands:
                return False, f"Command '{first_word}' not in allowed list"

        for pattern in self.forbidden_patterns:
            if pattern.search(command):
                return False, "Command contains forbidden pattern"

        parts = command.strip().split()
        if parts and parts[0] in self.DANGEROUS_COMMANDS:
            return False, f"Command '{parts[0]}' is not allowed"

        return True, None

    def sanitize(self, command: str) -> str:
        """Sanitize command by removing dangerous patterns."""
        sanitized = command
        for pattern in self.forbidden_patterns:
            sanitized = pattern.sub("[REMOVED]", sanitized)
        return sanitized


command_validator = CommandValidator()