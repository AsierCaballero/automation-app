"""Task model for automation tasks."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """Tag model for organizing tasks."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), default="#6366f1")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag(name={self.name})>"


class Task(Base):
    """Task model for automation tasks."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    command = Column(Text, nullable=False)
    task_type = Column(String(50), default="shell", index=True)
    status = Column(String(20), default="idle", index=True)
    last_output = Column(Text, nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True, index=True)
    timeout = Column(Integer, default=300)
    retry_attempts = Column(Integer, default=0)
    retry_delay = Column(Integer, default=5)

    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    schedules = relationship("Schedule", back_populates="task", cascade="all, delete-orphan")
    executions = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Task(name={self.name}, status={self.status})>"