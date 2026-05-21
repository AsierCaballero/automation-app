"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., format="email")
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[str] = Field(None, format="email")
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """User response schema."""

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""

    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str
    password: str


class TagBase(BaseModel):
    """Base tag schema."""

    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    description: Optional[str] = None


class TagCreate(TagBase):
    """Tag creation schema."""

    pass


class TagResponse(TagBase):
    """Tag response schema."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    """Base task schema."""

    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    command: str = Field(..., min_length=1)
    task_type: str = Field(default="shell")
    timeout: int = Field(default=300, ge=1, le=3600)
    retry_attempts: int = Field(default=0, ge=0, le=10)
    retry_delay: int = Field(default=5, ge=1, le=300)
    active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError("Name must contain only alphanumeric, underscore, or hyphen characters")
        return v.lower()


class TaskCreate(TaskBase):
    """Task creation schema."""

    tags: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    """Task update schema."""

    description: Optional[str] = None
    command: Optional[str] = Field(None, min_length=1)
    task_type: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=1, le=3600)
    retry_attempts: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=1, le=300)
    active: Optional[bool] = None
    tags: Optional[List[str]] = None


class TaskResponse(TaskBase):
    """Task response schema."""

    id: int
    status: str
    last_output: Optional[str]
    last_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Task list response schema."""

    id: int
    name: str
    description: Optional[str]
    task_type: str
    status: str
    last_run: Optional[datetime]
    active: bool
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class ExecutionLogBase(BaseModel):
    """Base execution log schema."""

    pass


class ExecutionLogResponse(BaseModel):
    """Execution log response schema."""

    id: int
    task_id: int
    task_name: str
    status: str
    output: Optional[str]
    error: Optional[str]
    return_code: Optional[int]
    duration_ms: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime]
    trigger_type: str
    triggered_by: Optional[str]

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    """Base schedule schema."""

    cron_expression: str = Field(..., pattern=r"^[^\s]+ [^\s]+ [^\s]+ [^\s]+ [^\s]+ [^\s]*$")
    description: Optional[str] = Field(None, max_length=255)
    enabled: bool = True
    timezone: str = Field(default="UTC")


class ScheduleCreate(ScheduleBase):
    """Schedule creation schema."""

    task_name: str


class ScheduleUpdate(BaseModel):
    """Schedule update schema."""

    cron_expression: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    timezone: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    """Schedule response schema."""

    id: int
    task_id: int
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookBase(BaseModel):
    """Base webhook schema."""

    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., format="uri")
    events: List[str] = Field(default=["task.success", "task.failed"])
    headers: dict = Field(default=dict)
    secret: Optional[str] = Field(None, min_length=16)
    enabled: bool = True
    timeout: int = Field(default=30, ge=5, le=120)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay: int = Field(default=5, ge=1, le=60)


class WebhookCreate(WebhookBase):
    """Webhook creation schema."""

    pass


class WebhookUpdate(BaseModel):
    """Webhook update schema."""

    url: Optional[str] = Field(None, format="uri")
    events: Optional[List[str]] = None
    headers: Optional[dict] = None
    secret: Optional[str] = Field(None, min_length=16)
    enabled: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=5, le=120)
    retry_attempts: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=1, le=60)


class WebhookResponse(WebhookBase):
    """Webhook response schema."""

    id: int
    last_triggered: Optional[datetime]
    last_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskRunResponse(BaseModel):
    """Task run response schema."""

    status: str
    output: Optional[str]
    execution_id: int
    duration_ms: Optional[int]


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    database: str
    scheduler: str
    timestamp: datetime