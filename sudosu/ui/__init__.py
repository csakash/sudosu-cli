"""Console UI helpers for Sudosu."""

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


console = Console()

# ══════════════════════════════════════════════════════════════════════════════
# COMMAND HISTORY - Enables up/down arrow navigation for previous commands
# ══════════════════════════════════════════════════════════════════════════════

def _get_history_file() -> Path:
    """Get the path to the command history file."""
    # Store history in ~/.sudosu/command_history (file, not directory)
    history_dir = Path.home() / ".sudosu"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir / "command_history"


# Global prompt session with persistent file history
_prompt_session: PromptSession | None = None


def _get_prompt_session() -> PromptSession:
    """Get or create the global prompt session with history."""
    global _prompt_session
    if _prompt_session is None:
        history_file = _get_history_file()
        _prompt_session = PromptSession(history=FileHistory(str(history_file)))
    return _prompt_session

# ══════════════════════════════════════════════════════════════════════════════
# SUDOSU BRAND COLORS
# ══════════════════════════════════════════════════════════════════════════════
COLOR_PRIMARY = "#FEEAC9"      # Warm cream/peach - Logo, main headings
COLOR_SECONDARY = "#FFCDC9"    # Light coral/pink - Section headings
COLOR_ACCENT = "#FD7979"       # Coral red - Warnings, important highlights
COLOR_INTERACTIVE = "#BDE3C3"  # Light blue - Commands, agent names, interactive elements

# Sudosu ASCII Art Logo
SUDOSU_LOGO = """
       ⣀⣀⣀⣀⣀⣀⣀⣀⣀       
    ⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦    
   ⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷   
  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿  
  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿  
 ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ 
 ⣿⣿⣿⣿⡿⠋⠁⠈⠙⢿⡿⠋⠁⠈⠻⣿⣿⣿⣿ 
 ⣿⣿⣿⣿⡇⠀⣿⣿⠀⢸⡇⠀⣿⣿⠀⢸⣿⣿⣿ 
 ⣿⣿⣿⣿⣷⣄⣀⣀⣠⣾⣷⣄⣀⣀⣠⣾⣿⣿⣿ 
 ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ 
  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿  
  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿  
   ⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟   
    ⠙⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠋    
       ⠉⠉⠉⠉⠉⠉⠉⠉⠉       
"""

# Simpler fallback ASCII logo using basic characters
# Matches the Sudosu logo: filled body with hollow circular eyes and connected ears
SUDOSU_LOGO_SIMPLE = """
    ▄▄      ▄▄
    ██▀▀▀▀▀▀▀▀██
    ████  ██  ████
    ██████████████
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""


def get_version() -> str:
    """Get Sudosu version."""
    try:
        from importlib.metadata import version
        return version("sudosu")
    except Exception:
        return "0.1.0"


def print_welcome(username: str = "User"):
    """Print welcome message with ASCII art logo - Claude Code style."""
    console.print()
    
    # Create the welcome box similar to Claude Code
    version = get_version()
    
    # Create a table for the layout (left: welcome + logo, right: tips)
    layout_table = Table.grid(padding=(0, 4))
    layout_table.add_column(justify="center", width=35)  # Left column for welcome + logo
    layout_table.add_column(justify="left")  # Right column for tips
    
    # Build left side content
    left_content = Text()
    left_content.append(f"Welcome back {username}!\n\n", style="bold white")
    left_content.append(SUDOSU_LOGO_SIMPLE, style=f"bold {COLOR_PRIMARY}")  # Primary color for logo
    left_content.append(f"\nv{version}", style="dim")
    
    # Build right side content (tips and recent activity)
    right_content = Text()
    right_content.append("Tips for getting started\n", style=f"bold {COLOR_SECONDARY}")  # Secondary for headings
    right_content.append("Type a message to chat with your AI agent\n", style="white")
    right_content.append("Use ", style="white")
    right_content.append("@agent_name", style=f"{COLOR_INTERACTIVE}")  # Interactive color for commands
    right_content.append(" to switch agents\n", style="white")
    right_content.append("Type ", style="white")
    right_content.append("/help", style=f"{COLOR_INTERACTIVE}")
    right_content.append(" for all commands\n\n", style="white")
    right_content.append("Recent activity\n", style=f"bold {COLOR_SECONDARY}")
    right_content.append("No recent activity", style="dim")
    
    layout_table.add_row(left_content, right_content)
    
    # Wrap in a panel with the title
    panel = Panel(
        layout_table,
        title=f"[bold {COLOR_PRIMARY}]Sudosu v{version}[/bold {COLOR_PRIMARY}]",
        title_align="left",
        border_style=COLOR_PRIMARY,
        padding=(1, 2),
    )
    
    console.print(panel)
    console.print()


def print_help():
    """Print help message."""
    table = Table(title="Sudosu Commands", border_style=COLOR_PRIMARY, title_style=f"bold {COLOR_PRIMARY}")
    table.add_column("Command", style=COLOR_INTERACTIVE)
    table.add_column("Description")
    
    commands = [
        ("/help", "Show this help message"),
        ("/agent", "List available agents"),
        ("/agent create <name>", "Create a new agent"),
        ("/agent delete <name>", "Delete an agent"),
        ("/memory", "Show conversation memory info"),
        ("/memory clear", "Clear conversation (fresh start)"),
        ("/back", "Return to sudosu from an agent"),
        ("/config", "Show current configuration"),
        ("/config set <key> <value>", "Set a configuration value"),
        ("/clear", "Clear the screen"),
        ("/quit", "Exit Sudosu"),
        ("", ""),
        ("── Integrations ──", ""),
        ("/connect gmail", "Connect your Gmail account"),
        ("/disconnect gmail", "Disconnect Gmail"),
        ("/integrations", "Show connected integrations"),
        ("", ""),
        ("@<agent> <message>", "Switch to and message an agent"),
        ("<message>", "Continue with current agent"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    console.print(table)
    console.print(f"\n[dim]💡 Tip: After sudosu routes you to an agent,\n   your follow-ups go to that agent automatically.[/dim]")


def print_agents(agents: list[dict]):
    """Print list of available agents in the current project."""
    if not agents:
        console.print(f"[{COLOR_ACCENT}]No agents found in this project.[/{COLOR_ACCENT}]")
        console.print(f"[dim]Create one with [{COLOR_INTERACTIVE}]/agent create <name>[/{COLOR_INTERACTIVE}][/dim]")
        console.print("[dim]Or type a message to chat with the default Sudosu assistant.[/dim]")
        return
    
    table = Table(title="Available Agents", border_style=COLOR_PRIMARY, title_style=f"bold {COLOR_PRIMARY}")
    table.add_column("Name", style=COLOR_INTERACTIVE)
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
    console.print(f"[bold {COLOR_ACCENT}]Error:[/bold {COLOR_ACCENT}] {escape(message)}", highlight=False)


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold {COLOR_INTERACTIVE}]✓[/bold {COLOR_INTERACTIVE}] {escape(message)}", highlight=False)


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold {COLOR_ACCENT}]⚠[/bold {COLOR_ACCENT}] {escape(message)}", highlight=False)


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold {COLOR_INTERACTIVE}]ℹ[/bold {COLOR_INTERACTIVE}] {escape(message)}", highlight=False)


def print_agent_thinking(agent_name: str):
    """Print agent thinking indicator.
    
    For the default 'sudosu' agent, just shows 'thinking...'
    For other agents, shows '@agent_name thinking...'
    """
    if agent_name.lower() == "sudosu":
        console.print(f"\n[bold {COLOR_PRIMARY}]thinking...[/bold {COLOR_PRIMARY}]\n")
    else:
        console.print(f"\n[bold {COLOR_PRIMARY}]@{agent_name}[/bold {COLOR_PRIMARY}] is thinking...\n")


def print_routing_to_agent(agent_name: str):
    """Print routing transition message."""
    console.print(f"\n[bold {COLOR_INTERACTIVE}]→ Routing to @{agent_name}...[/bold {COLOR_INTERACTIVE}]\n")


def print_consultation_route(from_agent: str, to_agent: str, reason: str):
    """Print consultation routing message."""
    console.print(f"\n[dim]💭 @{from_agent} consulted the orchestrator...[/dim]")
    console.print(f"[bold {COLOR_INTERACTIVE}]→ Handing off to @{to_agent}[/bold {COLOR_INTERACTIVE}]")
    console.print(f"[dim]   Reason: {reason}[/dim]\n")


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
            console.print(f"[{COLOR_INTERACTIVE}]✓ File saved: {result.get('path', 'unknown')}[/{COLOR_INTERACTIVE}]")
        elif tool_name == "read_file":
            # Don't print content, it goes to the agent
            pass
        elif tool_name == "list_directory":
            # Don't print listing, it goes to the agent
            pass
    elif "error" in result:
        console.print(f"[{COLOR_ACCENT}]✗ {result['error']}[/{COLOR_ACCENT}]")


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
    """Handles streaming text output with markdown rendering support.
    
    Modes:
    - render_markdown=True, show_streaming=False: Buffer all, render markdown at end (cleanest)
    - render_markdown=True, show_streaming=True: Show raw stream then render markdown (redundant but shows activity)
    - render_markdown=False: Print raw text as it streams (no formatting)
    """
    
    def __init__(self, render_markdown: bool = True, show_streaming: bool = False):
        self.buffer = ""
        self.render_markdown = render_markdown
        self.show_streaming = show_streaming
        self._chunk_count = 0
    
    def print_chunk(self, chunk: str):
        """Print a chunk of streaming text."""
        self._chunk_count += 1
        
        if self.render_markdown:
            # Buffer for final markdown rendering
            self.buffer += chunk
            
            if self.show_streaming:
                # Also show raw text as it streams (dimmed)
                console.print(chunk, end="", style="dim")
        else:
            # Raw mode: print directly without markdown processing
            console.print(chunk, end="")
    
    def flush(self):
        """Flush buffer and render as markdown."""
        if self.buffer:
            if self.render_markdown:
                if self.show_streaming:
                    # Add visual separator before formatted version
                    console.print("\n")
                    console.rule(style="dim blue")
                    console.print()
                
                # Render the complete response as formatted markdown
                md = Markdown(self.buffer.strip())
                console.print(md)
            else:
                # Just ensure newline at end for raw mode
                pass
            self.buffer = ""
        console.print()  # Final newline


class LiveStreamPrinter:
    """Streams text with live-updating markdown rendering.
    
    Uses Rich's Live display to progressively render markdown as chunks arrive.
    Provides the best experience: see formatted output as it streams.
    """
    
    def __init__(self):
        self.buffer = ""
        self._live: Live | None = None
    
    def start(self):
        """Start live display."""
        self._live = Live(
            Markdown(""),
            console=console,
            refresh_per_second=10,
            vertical_overflow="visible",
        )
        self._live.start()
    
    def print_chunk(self, chunk: str):
        """Add chunk and update live markdown display."""
        self.buffer += chunk
        if self._live:
            # Re-render markdown with updated content
            self._live.update(Markdown(self.buffer))
    
    def flush(self):
        """Stop live display and print final output."""
        if self._live:
            self._live.stop()
            self._live = None
        console.print()  # Final newline
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.flush()


def get_user_input(prompt: str = "> ") -> str:
    """Get user input with styled prompt and command history.
    
    Supports:
    - Up/Down arrows to navigate command history
    - History persisted to ~/.sudosu/command_history
    - Standard readline-style editing (Ctrl+A, Ctrl+E, etc.)
    
    Note: This is a sync wrapper. For async contexts, use get_user_input_async().
    """
    session = _get_prompt_session()
    # Use prompt_toolkit's HTML formatting for proper color support
    # COLOR_PRIMARY is #FEEAC9 (warm cream)
    styled_prompt = HTML(f'<style fg="#FEEAC9" bold="true">{prompt}</style>')
    
    # Check if we're in an async context
    import asyncio
    try:
        asyncio.get_running_loop()
        # We're in an async context - use a thread to avoid event loop conflicts
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(session.prompt, styled_prompt)
            return future.result()
    except RuntimeError:
        # No running loop - safe to use sync version
        return session.prompt(styled_prompt)


async def get_user_input_async(prompt: str = "> ") -> str:
    """Async version of get_user_input with command history.
    
    Use this in async contexts (like the main interactive loop).
    """
    session = _get_prompt_session()
    # Use prompt_toolkit's HTML formatting for proper color support
    # COLOR_PRIMARY is #FEEAC9 (warm cream)
    styled_prompt = HTML(f'<style fg="#FEEAC9" bold="true">{prompt}</style>')
    return await session.prompt_async(styled_prompt)


def get_user_confirmation(message: str) -> bool:
    """Get yes/no confirmation from user."""
    response = console.input(f"{message} [y/N]: ").strip().lower()
    return response in ("y", "yes")


def clear_screen():
    """Clear the terminal screen."""
    console.clear()
