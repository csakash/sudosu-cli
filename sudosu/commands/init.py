"""Init command handler."""

from pathlib import Path

from sudosu.core import ensure_config_structure, get_global_config_dir, set_config_value
from sudosu.ui import console, get_user_input, print_error, print_info, print_success


async def init_command():
    """Initialize Sudosu configuration."""
    console.print()
    console.print("[bold blue]🚀 Welcome to Sudosu![/bold blue]")
    console.print()
    
    config_dir = get_global_config_dir()
    
    if config_dir.exists():
        print_info(f"Configuration already exists at {config_dir}")
        console.print("[dim]Checking structure...[/dim]")
    
    # Ensure structure exists
    ensure_config_structure()
    
    console.print()
    print_success(f"Created {config_dir}/config.yaml")
    print_success(f"Created {config_dir}/agents/")
    print_success(f"Created {config_dir}/skills/")
    
    # Ask for backend URL
    console.print()
    print_info("Enter your backend URL (or press Enter for localhost)")
    backend_url = get_user_input("Backend URL [ws://localhost:8000/ws]: ").strip()
    
    if backend_url:
        set_config_value("backend_url", backend_url)
        print_success(f"Backend URL set to: {backend_url}")
    else:
        print_info("Using default: ws://localhost:8000/ws")
    
    console.print()
    print_success("Setup complete! Run 'sudosu' to start.")
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
