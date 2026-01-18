"""Init command handler."""

from pathlib import Path

from sudosu.core import ensure_config_structure, ensure_project_structure, get_global_config_dir
from sudosu.ui import console, print_info, print_success


async def init_command(silent: bool = False):
    """Initialize Sudosu configuration.
    
    Args:
        silent: If True, skip all prompts and use defaults (for auto-init)
    """
    config_dir = get_global_config_dir()
    
    # Ensure global config exists (just config.yaml)
    ensure_config_structure()
    
    if not silent:
        console.print()
        console.print("[bold blue]🚀 Welcome to Sudosu![/bold blue]")
        console.print()
        print_success(f"Global config created at {config_dir}/config.yaml")
        console.print()
        print_info("Run `sudosu` in any project folder to get started!")
        print_info("A .sudosu/ folder with your customizable AGENT.md will be created there.")
        console.print()


def init_project_command():
    """Initialize project-specific Sudosu configuration with AGENT.md."""
    cwd = Path.cwd()
    project_config = cwd / ".sudosu"
    
    if project_config.exists():
        print_info(f"Project configuration already exists at {project_config}")
        if not (project_config / "AGENT.md").exists():
            # Create AGENT.md if missing
            ensure_project_structure(cwd)
            print_success("Created .sudosu/AGENT.md")
        return
    
    # Create full project structure with AGENT.md
    ensure_project_structure(cwd)
    
    # Create context.md template
    context_file = project_config / "context.md"
    if not context_file.exists():
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
    print_success(f"Created {project_config}/AGENT.md (your customizable AI assistant)")
    print_success(f"Created {project_config}/agents/")
    print_success(f"Created {project_config}/context.md")
    print_info("Edit AGENT.md to customize your default AI assistant")
    print_info("Edit context.md to provide project context to all agents")
