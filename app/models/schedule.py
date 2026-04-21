"""Schedule model for task scheduling."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Schedule(Base):
    """Schedule model for task scheduling."""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    cron_expression = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True, index=True)
    timezone = Column(String(50), default="UTC")
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="schedules")

    def __repr__(self) -> str:
        return f"<Schedule(task_id={self.task_id}, cron={self.cron_expression})>"