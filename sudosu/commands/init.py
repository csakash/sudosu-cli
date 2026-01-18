"""Init command handler."""

from pathlib import Path

from sudosu.core import ensure_config_structure, get_global_config_dir
from sudosu.ui import console, print_info, print_success


async def init_command(silent: bool = False):
    """Initialize Sudosu configuration.
    
    Args:
        silent: If True, skip all prompts and use defaults (for auto-init)
    """
    config_dir = get_global_config_dir()
    
    # Ensure structure exists (creates config with production defaults)
    ensure_config_structure()
    
    if not silent:
        console.print()
        console.print("[bold blue]🚀 Welcome to Sudosu![/bold blue]")
        console.print()
        print_success(f"Configuration created at {config_dir}")
        console.print()
        print_success("Setup complete! You're ready to go.")
        console.print()


def init_project_command():
    """Initialize project-specific Sudosu configuration."""
    cwd = Path.cwd()
    project_config = cwd / ".sudosu"
    
    if project_config.exists():
        print_info(f"Project configuration already exists at {project_config}")
        return
    
    # Create structure
    (project_config / "agents").mkdir(parents=True, exist_ok=True)
    (project_config / "skills").mkdir(parents=True, exist_ok=True)
    
    # Create context.md template
    context_file = project_config / "context.md"
    context_file.write_text("""# Project Context

This file provides context about the project to all agents.

## Project Overview

Describe your project here...

## Key Files

- `src/` - Source code
- `docs/` - Documentation

## Guidelines

Any specific guidelines for agents working in this project...
""")
    
    print_success(f"Created {project_config}/")
    print_success(f"Created {project_config}/agents/")
    print_success(f"Created {project_config}/skills/")
    print_success(f"Created {project_config}/context.md")
    print_info("Edit context.md to provide project context to agents")
