"""Execution log model for task history."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExecutionLog(Base):
    """Execution log model for tracking task execution history."""

    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    return_code = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    trigger_type = Column(String(20), default="manual", index=True)
    triggered_by = Column(String(100), nullable=True)

    task = relationship("Task", back_populates="executions")

    def __repr__(self) -> str:
        return f"<ExecutionLog(task={self.task_name}, status={self.status})>"