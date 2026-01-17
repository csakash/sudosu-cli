"""Agent command handlers."""

import os
from pathlib import Path
from typing import Optional

import httpx

from sudosu.core import get_project_config_dir
from sudosu.core.agent_loader import (
    AGENT_TEMPLATES,
    create_agent_template,
    discover_agents,
    load_agent_config,
)
from sudosu.core.safety import is_safe_directory
from sudosu.ui import (
    console,
    get_user_confirmation,
    get_user_input,
    print_agents,
    print_error,
    print_info,
    print_success,
    print_warning,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_ACCENT,
    COLOR_INTERACTIVE,
)


# Backend URL for prompt refinement
BACKEND_URL = os.environ.get("SUDOSU_BACKEND_URL", "http://localhost:8000")


async def refine_prompt_via_backend(
    name: str,
    description: str,
    tools: list[str],
) -> tuple[str, str]:
    """Call the backend to refine an agent's system prompt.
    
    Args:
        name: Agent name
        description: Brief description from user
        tools: List of available tools
        
    Returns:
        Tuple of (refined_system_prompt, refined_description)
        Returns fallback values if backend is unavailable.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/refine-prompt",
                json={
                    "name": name,
                    "description": description,
                    "tools": tools,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["system_prompt"], data["refined_description"]
            else:
                # Backend returned an error, use fallback
                return None, None
                
    except Exception:
        # Backend unavailable, return None to signal fallback
        return None, None


def list_agents_command():
    """List all available agents (project-local only)."""
    agents = []
    
    # Get agents from project config only (no global agents)
    project_dir = get_project_config_dir()
    if project_dir:
        project_agents_dir = project_dir / "agents"
        if project_agents_dir.exists():
            agents = discover_agents(project_agents_dir)
            # Mark as project-specific with location
            for agent in agents:
                agent["_project"] = True
                agent["_location"] = ".sudosu"
    
    print_agents(agents)


def get_available_agents() -> list[dict]:
    """Get list of all available agents in current project."""
    agents = []
    project_dir = get_project_config_dir()
    if project_dir:
        project_agents_dir = project_dir / "agents"
        if project_agents_dir.exists():
            agents = discover_agents(project_agents_dir)
    return agents


async def create_agent_command(name: Optional[str] = None):
    """Create a new agent."""
    # Safety check - block home directory
    cwd = Path.cwd()
    is_safe, reason = is_safe_directory(cwd)
    
    if not is_safe:
        print_error(f"Cannot create agents from {reason}")
        print_info("Navigate to a project folder first:")
        console.print("[dim]  mkdir ~/my-project && cd ~/my-project[/dim]")
        return
    
    # Get agent name
    if not name:
        name = get_user_input("Agent name: ").strip().lower()
    
    if not name:
        print_error("Agent name cannot be empty")
        return
    
    # Validate name
    if not name.replace("-", "").replace("_", "").isalnum():
        print_error("Agent name can only contain letters, numbers, hyphens, and underscores")
        return
    
    # Always use current directory's .sudosu/agents/
    project_sudosu_dir = cwd / ".sudosu"
    agents_dir = project_sudosu_dir / "agents"
    
    # Auto-create .sudosu/ if it doesn't exist
    if not project_sudosu_dir.exists():
        project_sudosu_dir.mkdir()
        console.print(f"[{COLOR_INTERACTIVE}]✓[/{COLOR_INTERACTIVE}] Created .sudosu/ in current directory")
    
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if agent already exists in this project
    if (agents_dir / name).exists():
        print_error(f"Agent '{name}' already exists in this project")
        return
    
    # Check if we have a template
    if name in AGENT_TEMPLATES:
        template = AGENT_TEMPLATES[name]
        print_info(f"Using built-in template for '{name}'")
        description = template["description"]
        system_prompt = template["system_prompt"]
    else:
        # Ask for description
        print_info("What should this agent do?")
        description = get_user_input("Description: ").strip()
        
        if not description:
            description = f"A helpful assistant named {name}"
        
        # Default tools for the agent
        default_tools = ["read_file", "write_file", "list_directory"]
        
        # Refine the prompt via backend
        console.print("[dim]Crafting agent prompt...[/dim]")
        refined_prompt, refined_description = await refine_prompt_via_backend(
            name=name,
            description=description,
            tools=default_tools,
        )
        
        if refined_prompt:
            # Use the refined prompt from backend
            system_prompt = refined_prompt
            if refined_description:
                description = refined_description
            console.print(f"[{COLOR_INTERACTIVE}]✓[/{COLOR_INTERACTIVE}] Agent prompt refined")
        else:
            # Fallback to basic prompt if backend unavailable
            console.print(f"[{COLOR_ACCENT}]![/{COLOR_ACCENT}] [dim]Using basic prompt (backend unavailable)[/dim]")
            system_prompt = f"""# {name.replace('-', ' ').replace('_', ' ').title()} Agent

You are {description.lower()}.

## Guidelines

1. Be helpful and accurate
2. Ask clarifying questions when needed
3. Use markdown formatting for better readability
4. Save files when appropriate

## Tools Available

- **read_file**: Read content from files
- **write_file**: Write content to files  
- **list_directory**: List directory contents
"""
    
    # Create the agent
    try:
        agent_path = create_agent_template(
            agent_dir=agents_dir,
            name=name,
            description=description,
            system_prompt=system_prompt,
        )
        console.print(f"[{COLOR_INTERACTIVE}]✓[/{COLOR_INTERACTIVE}] Agent [{COLOR_PRIMARY}]'{name}'[/{COLOR_PRIMARY}] created at {agent_path}", highlight=False)
        console.print(f"[{COLOR_INTERACTIVE}]ℹ[/{COLOR_INTERACTIVE}] Use [{COLOR_PRIMARY}]@{name}[/{COLOR_PRIMARY}] to start chatting", highlight=False)
    except Exception as e:
        print_error(f"Failed to create agent: {e}")


async def delete_agent_command(name: Optional[str] = None):
    """Delete an agent (project-local only)."""
    if not name:
        name = get_user_input("Agent name to delete: ").strip().lower()
    
    if not name:
        print_error("Agent name cannot be empty")
        return
    
    # Find the agent in project directory only
    project_dir = get_project_config_dir()
    if not project_dir:
        print_error("No .sudosu/ folder found in current directory")
        print_info("You can only delete agents from a project with .sudosu/ folder")
        return
    
    agent_path = project_dir / "agents" / name
    
    if not agent_path.exists():
        print_error(f"Agent '{name}' not found in this project")
        return
    
    # Confirm deletion
    if not get_user_confirmation(f"Delete agent '{name}'?"):
        print_info("Cancelled")
        return
    
    # Delete
    import shutil
    try:
        shutil.rmtree(agent_path)
        console.print(f"[{COLOR_INTERACTIVE}]✓[/{COLOR_INTERACTIVE}] Agent [{COLOR_PRIMARY}]'{name}'[/{COLOR_PRIMARY}] deleted", highlight=False)
    except Exception as e:
        print_error(f"Failed to delete agent: {e}")


def get_agent_config(agent_name: str) -> Optional[dict]:
    """Load agent configuration by name (project-local only)."""
    agents_dirs = []
    
    # Only check project directory - no global agents
    project_dir = get_project_config_dir()
    if project_dir:
        agents_dirs.append(project_dir / "agents")
    
    if not agents_dirs:
        return None
    
    return load_agent_config(agent_name, agents_dirs)


async def handle_agent_command(args: list[str]):
    """Handle /agent command with subcommands."""
    if not args:
        list_agents_command()
        return
    
    subcommand = args[0].lower()
    
    if subcommand == "create":
        name = args[1] if len(args) > 1 else None
        await create_agent_command(name)
    
    elif subcommand == "delete":
        name = args[1] if len(args) > 1 else None
        await delete_agent_command(name)
    
    elif subcommand == "list":
        list_agents_command()
    
    else:
        print_error(f"Unknown subcommand: {subcommand}")
        print_info("Available: create, delete, list")
