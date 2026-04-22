"""Command-line interface for Automation App."""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from typing_extensions import Annotated

from app.core import init_db, setup_logging, get_logger
from app.core.database import get_db_context
from app.models import Task, User, Tag, ExecutionLog, Schedule
from app.services import (
    create_access_token, authenticate_user, execute_task,
    create_default_admin, get_password_hash,
)

app = typer.Typer(
    name="automation",
    help="Automation App CLI - DevOps automation with CLI + Web Dashboard",
    add_completion=False,
)
console = Console()
logger = get_logger("cli")


def get_user_auth() -> Optional[User]:
    """Get authenticated user from token file or environment."""
    import os

    token_file = os.path.expanduser("~/.automation_token")
    if os.path.exists(token_file):
        with open(token_file) as f:
            token = f.read().strip()
        if token:
            from app.services import decode_access_token
            token_data = decode_access_token(token)
            if token_data and token_data.username:
                with get_db_context() as db:
                    user = db.query(User).filter(User.username == token_data.username).first()
                    if user and user.is_active:
                        return user
    return None


@app.command()
def login(
    username: str = typer.Option(..., "--username", "-u", prompt=True),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    save_token: bool = typer.Option(True, "--save-token/--no-save-token"),
) -> None:
    """Authenticate and save token."""
    with get_db_context() as db:
        user = authenticate_user(db, username, password)
        if not user:
            console.print("[red]Invalid credentials[/red]")
            raise typer.Exit(1)

        token = create_access_token(data={"sub": user.username})
        console.print(f"[green]Logged in as {user.username}[/green]")

        if save_token:
            import os
            token_file = os.path.expanduser("~/.automation_token")
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, "w") as f:
                f.write(token)
            console.print("[dim]Token saved to ~/.automation_token[/dim]")


@app.command()
def logout() -> None:
    """Logout and remove saved token."""
    import os
    token_file = os.path.expanduser("~/.automation_token")
    if os.path.exists(token_file):
        os.remove(token_file)
        console.print("[green]Logged out successfully[/green]")
    else:
        console.print("[yellow]No token found[/yellow]")


@app.command()
def list(
    status_filter: Optional[str] = typer.Option(None, "--status", "-s"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t"),
    all_tasks: bool = typer.Option(False, "--all", "-a"),
) -> None:
    """List all tasks."""
    with get_db_context() as db:
        query = db.query(Task)
        if status_filter:
            query = query.filter(Task.status == status_filter)
        if tag:
            query = query.join(Task.tags).filter(Tag.name == tag)
        if not all_tasks:
            query = query.filter(Task.active == True)

        tasks = query.all()

        table = Table(title="Automation Tasks", show_lines=True)
        table.add_column("Name", style="cyan bold")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Last Run", style="blue")
        table.add_column("Active", style="green")

        for task in tasks:
            status_color = {
                "idle": "white",
                "running": "yellow",
                "success": "green",
                "failed": "red",
                "timeout": "red",
            }.get(task.status, "white")

            last_run = task.last_run.strftime("%Y-%m-%d %H:%M") if task.last_run else "Never"
            active = "[green]Yes[/green]" if task.active else "[red]No[/red]"

            table.add_row(
                task.name,
                task.task_type,
                f"[{status_color}]{task.status}[/{status_color}]",
                last_run,
                active,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(tasks)} tasks[/dim]")


@app.command()
def add(
    name: str = typer.Argument(..., help="Task name"),
    command: str = typer.Argument(..., help="Command to execute"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    task_type: str = typer.Option("shell", "--type", "-t"),
    timeout: int = typer.Option(300, "--timeout", min=1, max=3600),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
) -> None:
    """Add a new task."""
    from app.services import command_validator

    is_valid, error_msg = command_validator.validate(command)
    if not is_valid:
        console.print(f"[red]Invalid command: {error_msg}[/red]")
        raise typer.Exit(1)

    with get_db_context() as db:
        existing = db.query(Task).filter(Task.name == name.lower()).first()
        if existing:
            console.print(f"[red]Task '{name}' already exists[/red]")
            raise typer.Exit(1)

        task = Task(
            name=name.lower(),
            description=description,
            command=command,
            task_type=task_type,
            timeout=timeout,
        )
        db.add(task)
        db.flush()

        if tags:
            for tag_name in tags.split(","):
                tag_name = tag_name.strip()
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    db.flush()
                task.tags.append(tag)

        db.commit()
        console.print(f"[green]Task '{name}' created successfully[/green]")


@app.command()
def delete(name: str = typer.Argument(..., help="Task name")) -> None:
    """Delete a task."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        if not task:
            console.print(f"[red]Task '{name}' not found[/red]")
            raise typer.Exit(1)

        db.delete(task)
        db.commit()
        console.print(f"[green]Task '{name}' deleted[/green]")


@app.command()
def run(
    name: str = typer.Option(..., "--name", "-n", help="Task name"),
    show_output: bool = typer.Option(True, "--output/--no-output"),
) -> None:
    """Run a task."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        if not task:
            console.print(f"[red]Task '{name}' not found[/red]")
            raise typer.Exit(1)

        if not task.active:
            console.print(f"[red]Task '{name}' is disabled[/red]")
            raise typer.Exit(1)

        console.print(f"[blue]Running task: {task.name}[/blue]")
        task.status = "running"
        db.commit()

    result = execute_task(
        command=task.command,
        timeout=task.timeout,
        retry_attempts=task.retry_attempts,
        retry_delay=task.retry_delay,
        task_name=task.name,
    )

    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        task.status = "success" if result.success else "failed"
        task.last_output = result.output
        task.last_run = result.started_at if hasattr(result, 'started_at') else None
        db.commit()

        if result.success:
            console.print(f"[green]Task completed successfully ({result.duration_ms}ms)[/green]")
        else:
            console.print(f"[red]Task failed: {result.error}[/red]")

        if show_output and result.output:
            console.print(Panel(result.output, title=f"Output: {task.name}", expand=False))


@app.command()
def logs(
    name: str = typer.Argument(..., help="Task name"),
    lines: int = typer.Option(20, "--lines", "-n", min=1, max=1000),
    full: bool = typer.Option(False, "--full", "-f"),
) -> None:
    """View task logs."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        if not task:
            console.print(f"[red]Task '{name}' not found[/red]")
            raise typer.Exit(1)

        query = db.query(ExecutionLog).filter(ExecutionLog.task_name == name.lower())
        query = query.order_by(ExecutionLog.started_at.desc())

        if not full:
            query = query.limit(lines)

        execution_logs = query.all()

        if not execution_logs:
            console.print("[yellow]No execution logs found[/yellow]")
            return

        table = Table(title=f"Execution Logs: {name}", show_lines=True)
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Status", style="bold")
        table.add_column("Started", style="blue")
        table.add_column("Duration", style="magenta")
        table.add_column("Trigger", style="green")

        for log in execution_logs:
            status_style = {
                "success": "green",
                "failed": "red",
                "timeout": "red",
            }.get(log.status, "white")

            started = log.started_at.strftime("%Y-%m-%d %H:%M:%S") if log.started_at else "-"
            duration = f"{log.duration_ms}ms" if log.duration_ms else "-"

            table.add_row(
                str(log.id),
                f"[{status_style}]{log.status}[/{status_style}]",
                started,
                duration,
                log.trigger_type,
            )

        console.print(table)

        if full and execution_logs:
            latest = execution_logs[0]
            if latest.output:
                console.print(Panel(latest.output, title="Last Output", expand=False))


@app.command()
def show(name: str = typer.Argument(..., help="Task name")) -> None:
    """Show task details."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        if not task:
            console.print(f"[red]Task '{name}' not found[/red]")
            raise typer.Exit(1)

        tags = ", ".join([t.name for t in task.tags]) if task.tags else "None"

        info = f"""[cyan]Name:[/cyan] {task.name}
[cyan]Description:[/cyan] {task.description or 'N/A'}
[cyan]Command:[/cyan] {task.command}
[cyan]Type:[/cyan] {task.task_type}
[cyan]Status:[/cyan] {task.status}
[cyan]Timeout:[/cyan] {task.timeout}s
[cyan]Retry Attempts:[/cyan] {task.retry_attempts}
[cyan]Active:[/cyan] {'Yes' if task.active else 'No'}
[cyan]Tags:[/cyan] {tags}
[cyan]Created:[/cyan] {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}
[cyan]Last Run:[/cyan] {task.last_run.strftime('%Y-%m-%d %H:%M:%S') if task.last_run else 'Never'}"""

        console.print(Panel(info, title=f"Task: {name}", expand=False))


@app.command()
def schedule(
    task_name: str = typer.Option(..., "--task", "-n"),
    cron: str = typer.Option(..., "--cron", "-c", help="Cron expression"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    timezone: str = typer.Option("UTC", "--timezone", "-z"),
) -> None:
    """Create a schedule for a task."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == task_name.lower()).first()
        if not task:
            console.print(f"[red]Task '{task_name}' not found[/red]")
            raise typer.Exit(1)

        schedule = Schedule(
            task_id=task.id,
            cron_expression=cron,
            description=description,
            timezone=timezone,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        console.print(f"[green]Schedule created for task '{task_name}'[/green]")
        console.print(f"[dim]Schedule ID: {schedule.id}[/dim]")


@app.command()
def schedules() -> None:
    """List all schedules."""
    with get_db_context() as db:
        schedules = db.query(Schedule).all()

        if not schedules:
            console.print("[yellow]No schedules found[/yellow]")
            return

        table = Table(title="Scheduled Tasks", show_lines=True)
        table.add_column("ID", style="cyan")
        table.add_column("Task", style="bold")
        table.add_column("Cron", style="magenta")
        table.add_column("Enabled", style="green")
        table.add_column("Next Run", style="blue")

        for sched in schedules:
            task = db.query(Task).filter(Task.id == sched.task_id).first()
            task_name = task.name if task else f"Task#{sched.task_id}"
            enabled = "[green]Yes[/green]" if sched.enabled else "[red]No[/red]"
            next_run = sched.next_run.strftime("%Y-%m-%d %H:%M") if sched.next_run else "N/A"

            table.add_row(str(sched.id), task_name, sched.cron_expression, enabled, next_run)

        console.print(table)


@app.command()
def enable(name: str = typer.Argument(..., help="Task name")) -> None:
    """Enable a task."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        if not task:
            console.print(f"[red]Task '{name}' not found[/red]")
            raise typer.Exit(1)

        task.active = True
        db.commit()
        console.print(f"[green]Task '{name}' enabled[/green]")


@app.command()
def disable(name: str = typer.Argument(..., help="Task name")) -> None:
    """Disable a task."""
    with get_db_context() as db:
        task = db.query(Task).filter(Task.name == name.lower()).first()
        if not task:
            console.print(f"[red]Task '{name}' not found[/red]")
            raise typer.Exit(1)

        task.active = False
        db.commit()
        console.print(f"[green]Task '{name}' disabled[/green]")


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the web dashboard."""
    import uvicorn

    console.print(f"[blue]Starting Automation Dashboard on http://{host}:{port}[/blue]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    uvicorn.run(
        "app.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def init() -> None:
    """Initialize the database and create default admin."""
    init_db()
    with get_db_context() as db:
        create_default_admin(db)
    console.print("[green]Database initialized[/green]")
    console.print("[dim]Default admin credentials: admin / admin123[/dim]")


@app.command()
def user_add(
    username: str = typer.Option(..., "--username", "-u"),
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p"),
    full_name: Optional[str] = typer.Option(None, "--name", "-n"),
    admin: bool = typer.Option(False, "--admin"),
) -> None:
    """Add a new user (admin only)."""
    with get_db_context() as db:
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            console.print("[red]Username or email already exists[/red]")
            raise typer.Exit(1)

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_superuser=admin,
        )
        db.add(user)
        db.commit()
        console.print(f"[green]User '{username}' created[/green]")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()