"""CLI commands for managing background tasks.

IMPORTANT: These commands query the backend API.
All task execution happens SERVER-SIDE via ARQ workers.

The CLI is a THIN CLIENT - it only displays status and downloads reports.
"""

import asyncio
from datetime import datetime
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from sudosu.commands.integrations import get_user_id
from sudosu.core import get_backend_url

console = Console()
app = typer.Typer(help="Manage background tasks")

# Status emoji mapping
STATUS_EMOJI = {
    "pending": "⏳",
    "running": "🔄",
    "completed": "✅",
    "failed": "❌",
    "cancelled": "🚫",
}


def run_async(coro):
    """Run an async coroutine, handling both sync and async contexts.
    
    This helper detects if we're already in an event loop (like when called
    from the interactive CLI session) and uses the appropriate method.
    """
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running loop, use asyncio.run()
        return asyncio.run(coro)


def get_api_url() -> str:
    """Get the backend API URL for tasks."""
    backend_url = get_backend_url()
    # Convert ws:// to http:// for REST API
    if backend_url.startswith("ws://"):
        return backend_url.replace("ws://", "http://").replace("/ws", "")
    elif backend_url.startswith("wss://"):
        return backend_url.replace("wss://", "https://").replace("/ws", "")
    return backend_url.replace("/ws", "")


async def _list_tasks(status: Optional[str], limit: int) -> list[dict]:
    """Fetch tasks from backend API."""
    user_id = get_user_id()
    if not user_id:
        console.print("[red]Error: Not authenticated. Run 'sudosu init' first.[/red]")
        return []
    
    api_url = get_api_url()
    
    async with httpx.AsyncClient() as client:
        params = {"user_id": user_id, "limit": limit}
        if status and status != "all":
            params["status"] = status
        
        try:
            response = await client.get(
                f"{api_url}/api/tasks",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("tasks", [])
        except httpx.HTTPError as e:
            console.print(f"[red]Error fetching tasks: {e}[/red]")
            return []


async def _get_task(task_id: str) -> Optional[dict]:
    """Fetch a single task from backend API."""
    user_id = get_user_id()
    if not user_id:
        console.print("[red]Error: Not authenticated. Run 'sudosu init' first.[/red]")
        return None
    
    api_url = get_api_url()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{api_url}/api/tasks/{task_id}",
                params={"user_id": user_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print(f"[red]Task not found: {task_id}[/red]")
            else:
                console.print(f"[red]Error fetching task: {e}[/red]")
            return None
        except httpx.HTTPError as e:
            console.print(f"[red]Error fetching task: {e}[/red]")
            return None


async def _get_task_logs(task_id: str, limit: int = 50) -> list[dict]:
    """Fetch task logs from backend API."""
    user_id = get_user_id()
    if not user_id:
        return []
    
    api_url = get_api_url()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{api_url}/api/tasks/{task_id}/logs",
                params={"user_id": user_id, "limit": limit},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("logs", [])
        except httpx.HTTPError as e:
            console.print(f"[red]Error fetching logs: {e}[/red]")
            return []


async def _get_task_report(task_id: str) -> Optional[str]:
    """Fetch task report from backend API."""
    user_id = get_user_id()
    if not user_id:
        return None
    
    api_url = get_api_url()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{api_url}/api/tasks/{task_id}/report",
                params={"user_id": user_id},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("report")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                console.print(f"[yellow]Report not available for this task.[/yellow]")
            else:
                console.print(f"[red]Error fetching report: {e}[/red]")
            return None
        except httpx.HTTPError as e:
            console.print(f"[red]Error fetching report: {e}[/red]")
            return None


async def _cancel_task(task_id: str) -> bool:
    """Cancel a task via backend API."""
    user_id = get_user_id()
    if not user_id:
        console.print("[red]Error: Not authenticated. Run 'sudosu init' first.[/red]")
        return False
    
    api_url = get_api_url()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{api_url}/api/tasks/{task_id}/cancel",
                params={"user_id": user_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print(f"[red]Task not found: {task_id}[/red]")
            elif e.response.status_code == 400:
                console.print(f"[yellow]Task cannot be cancelled (already completed/failed).[/yellow]")
            else:
                console.print(f"[red]Error cancelling task: {e}[/red]")
            return False
        except httpx.HTTPError as e:
            console.print(f"[red]Error cancelling task: {e}[/red]")
            return False


def format_duration(seconds: int) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"


def format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp for display."""
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_str[:16]


@app.command("list")
def list_tasks(
    status: str = typer.Option(
        "all", 
        "--status", "-s", 
        help="Filter by status: all, pending, running, completed, failed, cancelled"
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of tasks to show"),
    full_id: bool = typer.Option(False, "--full-id", "-f", help="Show full task IDs"),
):
    """List your background tasks."""
    tasks = run_async(_list_tasks(status if status != "all" else None, limit))
    
    if not tasks:
        console.print("\n[dim]No background tasks found.[/dim]\n")
        return
    
    table = Table(title="Background Tasks", show_header=True, header_style="bold cyan")
    
    # Adjust ID column width based on full_id flag
    id_width = 36 if full_id else 12
    table.add_column("ID", style="dim", width=id_width)
    table.add_column("Status", width=12)
    table.add_column("Task Name", width=35)
    table.add_column("Progress", width=12)
    table.add_column("Created", width=16)
    
    for task in tasks:
        status_emoji = STATUS_EMOJI.get(task["status"], "❓")
        status_text = f"{status_emoji} {task['status']}"
        
        # Format progress
        if task["status"] == "running":
            progress = f"{task['progress_percent']:.0f}%"
        elif task["status"] == "completed":
            progress = f"✓ {task['completed_items']}/{task['total_items']}"
        elif task["status"] == "failed":
            progress = f"✗ {task['completed_items']}/{task['total_items']}"
        else:
            progress = "-"
        
        # Truncate task name
        task_name = task["task_name"]
        if len(task_name) > 33:
            task_name = task_name[:30] + "..."
        
        # Show full or truncated ID based on flag
        task_id_display = task["task_id"] if full_id else (task["task_id"][:12] + "...")
        
        table.add_row(
            task_id_display,
            status_text,
            task_name,
            progress,
            format_timestamp(task["created_at"]),
        )
    
    console.print()
    console.print(table)
    console.print()
    if not full_id:
        console.print("[dim]Use 'sudosu tasks status <task_id>' for details[/dim]")
        console.print("[dim]Use --full-id to show complete task IDs for copy/paste[/dim]")
    else:
        console.print("[dim]Use 'sudosu tasks status <task_id>' for details[/dim]")


@app.command("status")
def task_status(
    task_id: str = typer.Argument(..., help="Task ID (full or partial)"),
):
    """Get detailed status of a specific task."""
    # Handle partial task IDs
    if len(task_id) < 36:
        # Need to list and find matching task
        tasks = run_async(_list_tasks(None, 100))
        matches = [t for t in tasks if t["task_id"].startswith(task_id)]
        if len(matches) == 0:
            console.print(f"[red]No task found starting with '{task_id}'[/red]")
            return
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple tasks match '{task_id}':[/yellow]")
            for t in matches[:5]:
                console.print(f"  • {t['task_id'][:12]}... - {t['task_name'][:40]}")
            return
        task_id = matches[0]["task_id"]
    
    task = run_async(_get_task(task_id))
    if not task:
        return
    
    status_emoji = STATUS_EMOJI.get(task["status"], "❓")
    
    # Build status panel
    content = f"""
[bold]{task['task_name']}[/bold]

[cyan]Status:[/cyan] {status_emoji} {task['status'].upper()}
[cyan]Task ID:[/cyan] {task['task_id']}
[cyan]Type:[/cyan] {task['task_type']}

[cyan]Progress:[/cyan] {task['progress_percent']:.1f}%
[cyan]Items:[/cyan] {task['completed_items']} completed, {task['failed_items']} failed / {task['total_items']} total

[cyan]Created:[/cyan] {format_timestamp(task['created_at'])}
[cyan]Started:[/cyan] {format_timestamp(task.get('started_at', ''))}
[cyan]Completed:[/cyan] {format_timestamp(task.get('completed_at', ''))}
"""
    
    if task.get("error_message"):
        content += f"\n[red]Error:[/red] {task['error_message']}"
    
    console.print()
    console.print(Panel(content, title="Task Status", border_style="cyan"))
    console.print()
    
    # Show original prompt
    console.print("[bold]Original Request:[/bold]")
    console.print(Panel(task["original_prompt"], border_style="dim"))
    
    # Show result summary if completed
    if task.get("result_summary"):
        console.print("\n[bold]Result Summary:[/bold]")
        console.print(Panel(task["result_summary"], border_style="green"))
    
    console.print()
    console.print("[dim]Use 'sudosu tasks logs <task_id>' for execution logs[/dim]")


@app.command("logs")
def task_logs(
    task_id: str = typer.Argument(..., help="Task ID"),
    limit: int = typer.Option(50, "--limit", "-n", help="Number of logs to show"),
):
    """View task execution logs."""
    # Handle partial task IDs
    if len(task_id) < 36:
        tasks = run_async(_list_tasks(None, 100))
        matches = [t for t in tasks if t["task_id"].startswith(task_id)]
        if len(matches) == 1:
            task_id = matches[0]["task_id"]
        elif len(matches) == 0:
            console.print(f"[red]No task found starting with '{task_id}'[/red]")
            return
        else:
            console.print(f"[yellow]Multiple tasks match. Use more characters.[/yellow]")
            return
    
    logs = run_async(_get_task_logs(task_id, limit))
    
    if not logs:
        console.print("\n[dim]No logs found for this task.[/dim]\n")
        return
    
    console.print(f"\n[bold]Execution Logs[/bold] (Task: {task_id[:8]}...)\n")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Status", width=8)
    table.add_column("Tool", width=25)
    table.add_column("Message", width=40)
    table.add_column("Duration", width=10)
    
    for log in logs:
        status_icon = "✓" if log["status"] == "success" else "✗"
        status_style = "green" if log["status"] == "success" else "red"
        
        duration = f"{log['duration_ms']}ms" if log.get("duration_ms") else "-"
        message = log.get("message", "-")
        if len(message) > 38:
            message = message[:35] + "..."
        
        table.add_row(
            str(log["iteration"]),
            f"[{status_style}]{status_icon}[/{status_style}]",
            log.get("tool_name", "-"),
            message,
            duration,
        )
    
    console.print(table)
    console.print()


@app.command("report")
def task_report(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Download and display task report."""
    # Handle partial task IDs
    if len(task_id) < 36:
        tasks = run_async(_list_tasks(None, 100))
        matches = [t for t in tasks if t["task_id"].startswith(task_id)]
        if len(matches) == 1:
            task_id = matches[0]["task_id"]
        elif len(matches) == 0:
            console.print(f"[red]No task found starting with '{task_id}'[/red]")
            return
        else:
            console.print(f"[yellow]Multiple tasks match. Use more characters.[/yellow]")
            return
    
    report = run_async(_get_task_report(task_id))
    
    if not report:
        return
    
    console.print(f"\n[bold]Task Report[/bold] (ID: {task_id[:8]}...)\n")
    console.print(Panel(report, border_style="green"))
    console.print()


@app.command("cancel")
def cancel_task(
    task_id: str = typer.Argument(..., help="Task ID to cancel (full or partial)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Cancel a pending or running task.
    
    This will:
    - Mark the task as cancelled in the database
    - Stop execution at the next checkpoint (before the next tool call)
    - Prevent the task from running if it hasn't started yet
    
    Note: Tasks in the middle of a tool call will complete that call before stopping.
    """
    # Handle partial task IDs
    if len(task_id) < 36:
        tasks = run_async(_list_tasks(None, 100))
        matches = [t for t in tasks if t["task_id"].startswith(task_id)]
        if len(matches) == 1:
            task_id = matches[0]["task_id"]
        elif len(matches) == 0:
            console.print(f"[red]No task found starting with '{task_id}'[/red]")
            return
        else:
            console.print(f"[yellow]Multiple tasks match '{task_id}':[/yellow]")
            for t in matches[:5]:
                console.print(f"  • {t['task_id']} - {t['task_name'][:40]}")
            console.print(f"\n[dim]Use more characters to uniquely identify the task[/dim]")
            return
    
    # Get task details
    task = run_async(_get_task(task_id))
    if not task:
        return
    
    # Check if task can be cancelled
    if task["status"] not in ("pending", "running"):
        console.print(f"\n[yellow]This task cannot be cancelled (status: {task['status']})[/yellow]")
        console.print("[dim]Only pending or running tasks can be cancelled.[/dim]")
        return
    
    # Show confirmation unless force flag is set
    if not force:
        console.print(f"\n[yellow]⚠ Cancel this task?[/yellow]")
        console.print(f"  [bold]Task:[/bold] {task['task_name']}")
        console.print(f"  [bold]Status:[/bold] {task['status']}")
        console.print(f"  [bold]Progress:[/bold] {task['completed_items']}/{task['total_items']} items")
        console.print()
        
        confirm = typer.confirm("Cancel this task?", default=False)
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            return
    
    # Cancel the task
    success = run_async(_cancel_task(task_id))
    
    if success:
        console.print(f"\n[green]✓ Task cancelled successfully[/green]")
        console.print(f"  [bold]Task ID:[/bold] {task_id}")
        console.print()
        console.print("[cyan]What happens now:[/cyan]")
        if task["status"] == "pending":
            console.print("  • Task was not yet started - it will be skipped")
        else:
            console.print("  • Task will stop before the next tool call")
            console.print("  • Current operation will complete gracefully")
        console.print()
        console.print(f"[dim]Use 'sudosu tasks status {task_id[:12]}' to verify cancellation[/dim]")
    else:
        console.print(f"\n[red]✗ Failed to cancel task[/red]")
        console.print("[dim]The task may have already completed or been cancelled.[/dim]")


@app.command("watch")
def watch_task(
    task_id: str = typer.Argument(..., help="Task ID to watch"),
    interval: int = typer.Option(2, "--interval", "-i", help="Refresh interval in seconds"),
):
    """Watch task progress in real-time."""
    # Handle partial task IDs
    if len(task_id) < 36:
        tasks = run_async(_list_tasks(None, 100))
        matches = [t for t in tasks if t["task_id"].startswith(task_id)]
        if len(matches) == 1:
            task_id = matches[0]["task_id"]
        elif len(matches) == 0:
            console.print(f"[red]No task found starting with '{task_id}'[/red]")
            return
        else:
            console.print(f"[yellow]Multiple tasks match. Use more characters.[/yellow]")
            return
    
    console.print(f"\n[bold]Watching task {task_id[:8]}...[/bold]")
    console.print("[dim]Press Ctrl+C to stop watching[/dim]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            progress_task = progress.add_task("Progress", total=100)
            
            while True:
                task = run_async(_get_task(task_id))
                if not task:
                    break
                
                status = task["status"]
                percent = task["progress_percent"]
                
                progress.update(
                    progress_task, 
                    completed=percent,
                    description=f"{STATUS_EMOJI.get(status, '❓')} {task['task_name'][:40]}..."
                )
                
                # Stop watching if task is done
                if status in ("completed", "failed", "cancelled"):
                    progress.update(progress_task, completed=100)
                    break
                
                import time
                time.sleep(interval)
        
        # Show final status
        task = run_async(_get_task(task_id))
        if task:
            console.print()
            if task["status"] == "completed":
                console.print(f"[green]✓ Task completed successfully![/green]")
            elif task["status"] == "failed":
                console.print(f"[red]✗ Task failed: {task.get('error_message', 'Unknown error')}[/red]")
            elif task["status"] == "cancelled":
                console.print(f"[yellow]⚠ Task was cancelled[/yellow]")
            
            console.print(f"\n[dim]Use 'sudosu tasks status {task_id[:8]}' for details[/dim]")
    
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")


def handle_tasks_command(args: list[str]):
    """Handle the tasks command from main CLI."""
    if not args:
        # Default to list with explicit default values
        tasks = run_async(_list_tasks(None, 10))
        
        if not tasks:
            console.print("\n[dim]No background tasks found.[/dim]\n")
            return
        
        table = Table(title="Background Tasks", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Status", width=12)
        table.add_column("Task Name", width=35)
        table.add_column("Progress", width=12)
        table.add_column("Created", width=16)
        
        for task in tasks:
            status_emoji = STATUS_EMOJI.get(task["status"], "❓")
            status_text = f"{status_emoji} {task['status']}"
            
            # Format progress
            if task["status"] == "running":
                progress = f"{task['progress_percent']:.0f}%"
            elif task["status"] == "completed":
                progress = f"✓ {task['completed_items']}/{task['total_items']}"
            elif task["status"] == "failed":
                progress = f"✗ {task['completed_items']}/{task['total_items']}"
            else:
                progress = "-"
            
            # Truncate task name
            task_name = task["task_name"]
            if len(task_name) > 33:
                task_name = task_name[:30] + "..."
            
            table.add_row(
                task["task_id"][:8] + "...",
                status_text,
                task_name,
                progress,
                format_timestamp(task["created_at"]),
            )
        
        console.print()
        console.print(table)
        console.print()
        console.print("[dim]Use '/tasks status <task_id>' for details[/dim]")
    else:
        # Pass args to typer app for subcommands
        app(args)
