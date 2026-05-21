"""Webhook model for notifications."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Webhook(Base):
    """Webhook model for notifications."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    url = Column(Text, nullable=False)
    events = Column(JSON, default=list)
    headers = Column(JSON, default=dict)
    secret = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True, index=True)
    timeout = Column(Integer, default=30)
    retry_attempts = Column(Integer, default=3)
    retry_delay = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    last_status = Column(String(20), nullable=True)
    last_response = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Webhook(name={self.name}, url={self.url})>"