"""Scheduling service using APScheduler."""

from typing import Optional, Dict, Any
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("scheduler")


class SchedulerService:
    """Manage task scheduling with APScheduler."""

    def __init__(self) -> None:
        self.scheduler: Optional[BackgroundScheduler] = None
        self._running = False

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        executors = {
            "default": ThreadPoolExecutor(20),
        }
        jobstores = {
            "default": MemoryJobStore(),
        }
        job_defaults = {
            "coalesce": False,
            "max_instances": 3,
        }

        self.scheduler = BackgroundScheduler(
            executors=executors,
            jobstores=jobstores,
            job_defaults=job_defaults,
            timezone=settings.scheduler_timezone,
        )
        self.scheduler.start()
        self._running = True
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler and self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped")

    def add_job(
        self,
        job_id: str,
        func,
        cron_expression: str,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        timezone: str = "UTC",
    ) -> bool:
        """Add a scheduled job."""
        if not self.scheduler:
            return False

        try:
            parts = cron_expression.split()
            if len(parts) >= 5:
                minute, hour, day, month, day_of_week = parts[:5]
            else:
                logger.error(f"Invalid cron expression: {cron_expression}")
                return False

            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=timezone,
            )

            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True,
            )
            logger.info(f"Added scheduled job: {job_id} with cron: {cron_expression}")
            return True
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {str(e)}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        if not self.scheduler:
            return False

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details."""
        if not self.scheduler:
            return None

        job = self.scheduler.get_job(job_id)
        if job:
            return {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "pending": job.pending,
            }
        return None

    def get_all_jobs(self) -> list:
        """Get all scheduled jobs."""
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


scheduler_service = SchedulerService()