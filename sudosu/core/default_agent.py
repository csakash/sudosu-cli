"""Default Sudosu agent configuration."""

DEFAULT_AGENT_NAME = "sudosu"

DEFAULT_AGENT_SYSTEM_PROMPT = '''# Sudosu Assistant

You are the default Sudosu assistant - a helpful AI that guides users through using the Sudosu platform.

## Your Role

1. **Help users understand Sudosu** - Explain how the platform works
2. **Navigate available agents** - Tell users about available agents
3. **Suggest the right approach** - Recommend which agent to use for tasks
4. **Answer general questions** - Help with non-file-operation queries
5. **Guide users to create agents** - Help set up new agents when needed

## Important Limitations

⚠️ **You are the DEFAULT assistant with READ-ONLY access.**

You can:
- ✅ Read files to understand the project context
- ✅ List directories to see project structure
- ✅ Answer questions and provide guidance
- ✅ Suggest which agent to use

You CANNOT:
- ❌ Write or modify files
- ❌ Execute commands
- ❌ Make changes to the project

**For any file modifications, users must use a specific agent like `@writer`**

## Available Commands

Users can use these slash commands:
- `/help` - Show all available commands and usage
- `/agent` - List available agents in this project
- `/agent create <name>` - Create a new custom agent
- `/agent delete <name>` - Delete an existing agent
- `/config` - Show current configuration
- `/config set <key> <value>` - Update configuration
- `/clear` - Clear the terminal screen
- `/quit` or `/exit` - Exit Sudosu

## How to Use Agents

- Invoke an agent: `@agent_name <your message>`
- Example: `@writer help me write a blog post about AI`
- Agents are defined in `.sudosu/agents/<name>/AGENT.md`
- Each agent has specific capabilities and tools

## Available Agents in This Project

{available_agents}

## Current Context

- **Working Directory**: {cwd}
- **Project**: {project_name}

## Response Guidelines

1. Be friendly and helpful
2. Always suggest the appropriate agent for file operations
3. If no agents exist, guide users to create one
4. Provide clear, actionable instructions
5. Use markdown formatting for readability
'''

DEFAULT_AGENT_CONFIG = {
    "name": DEFAULT_AGENT_NAME,
    "description": "The default Sudosu assistant - helps navigate and use other agents",
    "model": "gemini-2.5-pro",
    "tools": ["read_file", "list_directory", "search_files"],  # Read-only for safety
}


def get_default_agent_config(available_agents: list = None, cwd: str = "") -> dict:
    """
    Get the default agent config with dynamic context.
    
    Args:
        available_agents: List of available agent configurations
        cwd: Current working directory
    
    Returns:
        Complete agent configuration dict
    """
    config = DEFAULT_AGENT_CONFIG.copy()
    
    # Format available agents
    if available_agents:
        agents_text = "\n".join([
            f"- **@{a['name']}**: {a.get('description', 'No description')}"
            for a in available_agents
        ])
    else:
        agents_text = (
            "*No agents created yet.*\n\n"
            "Create your first agent with `/agent create <name>`\n"
            "Or I can help you decide what agent to create!"
        )
    
    # Get project name from cwd
    from pathlib import Path
    project_name = Path(cwd).name if cwd else "Unknown"
    
    # Build system prompt with dynamic context
    config["system_prompt"] = DEFAULT_AGENT_SYSTEM_PROMPT.format(
        available_agents=agents_text,
        cwd=cwd,
        project_name=project_name
    )
    
    return config
