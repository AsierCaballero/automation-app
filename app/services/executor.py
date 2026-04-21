"""Task executor service with retry logic."""

import subprocess
import time
from datetime import datetime
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.core.logging import get_logger
from app.services.command_validator import command_validator

logger = get_logger("executor")


class ExecutionResult:
    """Result of task execution."""

    def __init__(
        self,
        success: bool,
        output: str,
        error: Optional[str] = None,
        return_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        self.success = success
        self.output = output
        self.error = error
        self.return_code = return_code
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "return_code": self.return_code,
            "duration_ms": self.duration_ms,
        }


def execute_task(
    command: str,
    timeout: int = 300,
    retry_attempts: int = 0,
    retry_delay: int = 5,
    task_name: Optional[str] = None,
) -> ExecutionResult:
    """Execute a shell command with timeout and retry logic."""
    is_valid, error_msg = command_validator.validate(command)
    if not is_valid:
        logger.error(f"Invalid command: {error_msg}")
        return ExecutionResult(
            success=False,
            output="",
            error=f"Command validation failed: {error_msg}",
        )

    sanitized_command = command_validator.sanitize(command)
    logger.info(f"Executing task: {task_name or 'unknown'} - Command: {sanitized_command[:100]}")

    attempt = 0
    max_attempts = retry_attempts + 1

    while attempt < max_attempts:
        attempt += 1
        if attempt > 1:
            logger.info(f"Retry attempt {attempt}/{max_attempts} for task: {task_name}")
            time.sleep(retry_delay)

        start_time = datetime.utcnow()
        try:
            result = subprocess.run(
                sanitized_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            output = result.stdout if result.stdout else ""
            if result.stderr:
                output += "\nSTDERR:\n" + result.stderr

            success = result.returncode == 0

            if success:
                logger.info(f"Task {task_name} completed successfully in {duration_ms}ms")
            else:
                logger.warning(
                    f"Task {task_name} failed with return code {result.returncode}"
                )

            return ExecutionResult(
                success=success,
                output=output,
                return_code=result.returncode,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            logger.error(f"Task {task_name} timed out after {timeout}s")

            if attempt < max_attempts:
                continue

            return ExecutionResult(
                success=False,
                output="",
                error=f"Task exceeded timeout of {timeout} seconds",
                return_code=-1,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.exception(f"Task {task_name} execution error: {str(e)}")

            if attempt < max_attempts:
                continue

            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1,
            )

    return ExecutionResult(
        success=False,
        output="",
        error="Max retry attempts exceeded",
    )


def validate_command(command: str) -> tuple[bool, Optional[str]]:
    """Validate a command string."""
    return command_validator.validate(command)