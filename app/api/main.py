"""FastAPI application with all endpoints."""

from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core import settings, init_db, setup_logging, get_logger
from app.core.database import get_db
from app.models import Task, User, Tag, ExecutionLog, Schedule, Webhook
from app.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskRunResponse,
    TagCreate, TagResponse,
    ExecutionLogResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    WebhookCreate, WebhookUpdate, WebhookResponse,
    UserCreate, UserResponse, UserUpdate,
    LoginRequest, Token,
    HealthResponse,
)
from app.services import (
    authenticate_user, create_access_token, create_default_admin,
    execute_task, command_validator,
    scheduler_service, webhook_service,
)
from app.api.deps import get_current_user, get_admin_user, get_optional_user

logger = setup_logging("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    init_db()

    with get_db() as db:
        create_default_admin(db)

    if settings.enable_scheduling:
        scheduler_service.start()
        logger.info("Scheduler service started")

    yield

    if scheduler_service.is_running():
        scheduler_service.stop()
        logger.info("Scheduler service stopped")


app = FastAPI(
    title="Automation API",
    description="DevOps automation CLI + Web Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

BASE_DIR = settings.get_base_dir()


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="connected",
        scheduler="running" if scheduler_service.is_running() else "stopped",
        timestamp=datetime.utcnow(),
    )


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    from app.services.auth import get_password_hash

    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/me", response_model=UserResponse, tags=["Users"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.get("/tags", response_model=List[TagResponse], tags=["Tags"])
async def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tags."""
    tags = db.query(Tag).all()
    return tags


@app.post("/tags", response_model=TagResponse, tags=["Tags"])
async def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new tag."""
    existing = db.query(Tag).filter(Tag.name == tag_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(**tag_data.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@app.get("/tasks", response_model=List[TaskListResponse], tags=["Tasks"])
async def list_tasks(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    tag: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
):
    """List all tasks with optional filtering."""
    query = db.query(Task)

    if active_only:
        query = query.filter(Task.active == True)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if tag:
        query = query.join(Task.tags).filter(Tag.name == tag)

    tasks = query.order_by(desc(Task.updated_at)).offset(skip).limit(limit).all()
    return tasks


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task."""
    is_valid, error_msg = command_validator.validate(task_data.command)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    existing = db.query(Task).filter(Task.name == task_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Task already exists")

    task_dict = task_data.model_dump(exclude={"tags"})
    task = Task(**task_dict)
    db.add(task)
    db.flush()

    if task_data.tags:
        for tag_name in task_data.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            task.tags.append(tag)

    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks/{name}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task details."""
    task = db.query(Task).filter(Task.name == name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{name}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(
    name: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task."""
    task = db.query(Task).filter(Task.name == name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_data.model_dump(exclude_unset=True, exclude={"tags"})

    if "command" in update_data:
        is_valid, error_msg = command_validator.validate(update_data["command"])
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    for key, value in update_data.items():
        setattr(task, key, value)

    if task_data.tags is not None:
        task.tags = []
        for tag_name in task_data.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            task.tags.append(tag)

    db.commit()
    db.refresh(task)
    return task


@app.post("/tasks/{name}/run", response_model=TaskRunResponse, tags=["Tasks"])
async def run_task(
    name: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Execute a task."""
    task = db.query(Task).filter(Task.name == name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.active:
        raise HTTPException(status_code=400, detail="Task is disabled")

    task.status = "running"
    db.commit()

    result = execute_task(
        command=task.command,
        timeout=task.timeout,
        retry_attempts=task.retry_attempts,
        retry_delay=task.retry_delay,
        task_name=task.name,
    )

    execution_log = ExecutionLog(
        task_id=task.id,
        task_name=task.name,
        status="success" if result.success else "failed",
        output=result.output,
        error=result.error,
        return_code=result.return_code,
        duration_ms=result.duration_ms,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        trigger_type="manual",
        triggered_by=current_user.username if current_user else "anonymous",
    )
    db.add(execution_log)

    task.status = "success" if result.success else "failed"
    task.last_output = result.output
    task.last_run = datetime.utcnow()
    db.commit()
    db.refresh(execution_log)

    if settings.enable_webhooks:
        webhooks = db.query(Webhook).filter(
            Webhook.enabled == True,
        ).all()

        for webhook in webhooks:
            event_match = (
                ("task.success" if result.success else "task.failed") in webhook.events
            )
            if event_match:
                if result.success:
                    await webhook_service.notify_task_success(
                        webhook_url=webhook.url,
                        task_name=task.name,
                        output=result.output,
                        duration_ms=result.duration_ms,
                        triggered_by=current_user.username if current_user else None,
                        headers=webhook.headers,
                        secret=webhook.secret,
                    )
                else:
                    await webhook_service.notify_task_failure(
                        webhook_url=webhook.url,
                        task_name=task.name,
                        error=result.error or "Unknown error",
                        duration_ms=result.duration_ms,
                        triggered_by=current_user.username if current_user else None,
                        headers=webhook.headers,
                        secret=webhook.secret,
                    )

    return TaskRunResponse(
        status=task.status,
        output=result.output,
        execution_id=execution_log.id,
        duration_ms=result.duration_ms,
    )


@app.delete("/tasks/{name}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
async def delete_task(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a task."""
    task = db.query(Task).filter(Task.name == name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    schedules = db.query(Schedule).filter(Schedule.task_id == task.id).all()
    for schedule in schedules:
        scheduler_service.remove_job(f"task_schedule_{schedule.id}")

    db.delete(task)
    db.commit()


@app.get("/tasks/{name}/logs", response_model=List[ExecutionLogResponse], tags=["Tasks"])
async def get_task_logs(
    name: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task execution history."""
    task = db.query(Task).filter(Task.name == name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.task_id == task.id)
        .order_by(desc(ExecutionLog.started_at))
        .limit(limit)
        .all()
    )
    return logs


@app.get("/schedules", response_model=List[ScheduleResponse], tags=["Schedules"])
async def list_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all schedules."""
    schedules = db.query(Schedule).all()
    return schedules


@app.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED, tags=["Schedules"])
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new schedule."""
    task = db.query(Task).filter(Task.name == schedule_data.task_name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    schedule = Schedule(
        task_id=task.id,
        cron_expression=schedule_data.cron_expression,
        description=schedule_data.description,
        enabled=schedule_data.enabled,
        timezone=schedule_data.timezone,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    def run_scheduled_task():
        with get_db() as session:
            task_obj = session.query(Task).filter(Task.id == task.id).first()
            if task_obj and task_obj.active:
                result = execute_task(
                    command=task_obj.command,
                    timeout=task_obj.timeout,
                    retry_attempts=task_obj.retry_attempts,
                    retry_delay=task_obj.retry_delay,
                    task_name=task_obj.name,
                )
                task_obj.status = "success" if result.success else "failed"
                task_obj.last_output = result.output
                task_obj.last_run = datetime.utcnow()

                log = ExecutionLog(
                    task_id=task_obj.id,
                    task_name=task_obj.name,
                    status=task_obj.status,
                    output=result.output,
                    error=result.error,
                    return_code=result.return_code,
                    duration_ms=result.duration_ms,
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                    trigger_type="scheduled",
                    triggered_by="scheduler",
                )
                session.add(log)
                session.commit()

    scheduler_service.add_job(
        job_id=f"task_schedule_{schedule.id}",
        func=run_scheduled_task,
        cron_expression=schedule.cron_expression,
        timezone=schedule.timezone,
    )

    return schedule


@app.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Schedules"])
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    scheduler_service.remove_job(f"task_schedule_{schedule.id}")
    db.delete(schedule)
    db.commit()


@app.get("/webhooks", response_model=List[WebhookResponse], tags=["Webhooks"])
async def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all webhooks."""
    webhooks = db.query(Webhook).all()
    return webhooks


@app.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED, tags=["Webhooks"])
async def create_webhook(
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new webhook."""
    webhook = Webhook(**webhook_data.model_dump())
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@app.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Webhooks"])
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint serving dashboard."""
    dashboard_path = BASE_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"message": "Automation API", "version": "1.0.0"}


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """Dashboard endpoint."""
    return FileResponse(str(BASE_DIR / "dashboard.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)