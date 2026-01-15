"""Safety checks for Sudosu operations."""

from pathlib import Path


def is_safe_directory(cwd: Path = None) -> tuple[bool, str]:
    """
    Check if the current directory is safe for Sudosu operations.
    
    Sudosu should not run from:
    - Home directory (~) - could expose sensitive dotfiles
    - Root directory (/) - system-wide access
    - System directories (/etc, /var, etc.)
    
    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    cwd = cwd or Path.cwd()
    home = Path.home()
    
    # Block home directory
    if cwd == home:
        return False, "home directory (~)"
    
    # Block root
    if cwd == Path("/"):
        return False, "root directory (/)"
    
    # Block common system directories
    unsafe_paths = ["/tmp", "/var", "/etc", "/usr", "/bin", "/sbin", "/opt"]
    cwd_str = str(cwd)
    for unsafe in unsafe_paths:
        if cwd_str == unsafe or cwd_str.startswith(unsafe + "/"):
            return False, f"system directory ({unsafe})"
    
    return True, ""


def get_safety_warning(reason: str) -> str:
    """Get a warning message for unsafe directories."""
    return f"""
⚠️  [bold yellow]Sudosu Safety Warning[/bold yellow]

You are running Sudosu from your [bold]{reason}[/bold].

For security reasons, Sudosu agents can [bold red]read and write files[/bold red] in your 
current directory. Running from this location could expose sensitive files
or cause unintended modifications.

[bold cyan]📁 Recommended Actions:[/bold cyan]

  1. [green]Create a project folder:[/green]
     [dim]mkdir ~/my-project && cd ~/my-project[/dim]
     
  2. [green]Or navigate to an existing project:[/green]
     [dim]cd ~/projects/my-app[/dim]
     
  3. [green]Then run Sudosu:[/green]
     [dim]sudosu[/dim]

[dim]Sudosu will only operate within the folder you start it from.[/dim]
"""


def is_home_directory(cwd: Path = None) -> bool:
    """Check if the current directory is the home directory."""
    cwd = cwd or Path.cwd()
    return cwd == Path.home()
