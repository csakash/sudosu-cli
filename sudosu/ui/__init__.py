"""Console UI helpers for Sudosu."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


console = Console()


def print_welcome():
    """Print welcome message."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]Welcome to Sudosu[/bold blue] 🚀\n"
        "[dim]Terminal-based AI Agent Platform[/dim]",
        border_style="blue",
    ))
    console.print()
    console.print("[dim]Just type a message to chat, or use @agent_name for specific agents[/dim]")
    console.print("[dim]Type /help for commands[/dim]")
    console.print()


def print_help():
    """Print help message."""
    table = Table(title="Sudosu Commands", border_style="blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    
    commands = [
        ("/help", "Show this help message"),
        ("/agent", "List available agents"),
        ("/agent create <name>", "Create a new agent"),
        ("/agent delete <name>", "Delete an agent"),
        ("/config", "Show current configuration"),
        ("/config set <key> <value>", "Set a configuration value"),
        ("/clear", "Clear the screen"),
        ("/quit", "Exit Sudosu"),
        ("@<agent> <message>", "Send a message to an agent"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    console.print(table)


def print_agents(agents: list[dict]):
    """Print list of available agents in the current project."""
    if not agents:
        console.print("[yellow]No agents found in this project.[/yellow]")
        console.print("[dim]Create one with /agent create <name>[/dim]")
        console.print("[dim]Or type a message to chat with the default Sudosu assistant.[/dim]")
        return
    
    table = Table(title="Available Agents", border_style="green")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Model", style="dim")
    
    for agent in agents:
        table.add_row(
            f"@{agent['name']}",
            agent.get("description", "No description"),
            agent.get("model", "gemini-2.5-pro"),
        )
    
    console.print(table)
    console.print("\n[dim]Agents are stored in .sudosu/agents/[/dim]")


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_agent_thinking(agent_name: str):
    """Print agent thinking indicator."""
    console.print(f"\n[bold cyan]🤖 {agent_name}[/bold cyan] is thinking...\n")


def print_tool_execution(tool_name: str, args: dict):
    """Print tool execution info."""
    if tool_name == "write_file":
        path = args.get("path", "file")
        console.print(f"[dim]📝 Writing to {path}...[/dim]")
    elif tool_name == "read_file":
        path = args.get("path", "file")
        console.print(f"[dim]📖 Reading {path}...[/dim]")
    elif tool_name == "list_directory":
        path = args.get("path", ".")
        console.print(f"[dim]📁 Listing {path}...[/dim]")
    elif tool_name == "run_command":
        cmd = args.get("command", "command")
        console.print(f"[dim]⚡ Running: {cmd}[/dim]")
    else:
        console.print(f"[dim]🔧 Executing {tool_name}...[/dim]")


def print_tool_result(tool_name: str, result: dict):
    """Print tool execution result."""
    if result.get("success"):
        if tool_name == "write_file":
            console.print(f"[green]✓ File saved: {result.get('path', 'unknown')}[/green]")
        elif tool_name == "read_file":
            # Don't print content, it goes to the agent
            pass
        elif tool_name == "list_directory":
            # Don't print listing, it goes to the agent
            pass
    elif "error" in result:
        console.print(f"[red]✗ {result['error']}[/red]")


def print_markdown(content: str):
    """Print markdown content."""
    md = Markdown(content)
    console.print(md)


def print_code(code: str, language: str = "python"):
    """Print syntax-highlighted code."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def create_spinner(message: str = "Processing..."):
    """Create a spinner progress indicator."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


class StreamPrinter:
    """Handles streaming text output."""
    
    def __init__(self):
        self.buffer = ""
        self.in_code_block = False
        self.code_language = ""
        self.code_buffer = ""
    
    def print_chunk(self, chunk: str):
        """Print a chunk of streaming text."""
        # For now, just print directly
        # TODO: Buffer and handle markdown rendering
        console.print(chunk, end="")
    
    def flush(self):
        """Flush any remaining buffer."""
        if self.buffer:
            console.print(self.buffer, end="")
            self.buffer = ""
        console.print()  # New line at end


def get_user_input(prompt: str = "> ") -> str:
    """Get user input with styled prompt."""
    return console.input(f"[bold green]{prompt}[/bold green]")


def get_user_confirmation(message: str) -> bool:
    """Get yes/no confirmation from user."""
    response = console.input(f"{message} [y/N]: ").strip().lower()
    return response in ("y", "yes")


def clear_screen():
    """Clear the terminal screen."""
    console.clear()
