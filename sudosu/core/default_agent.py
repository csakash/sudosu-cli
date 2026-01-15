"""Default Sudosu agent configuration."""

DEFAULT_AGENT_NAME = "sudosu"

DEFAULT_AGENT_SYSTEM_PROMPT = '''# Sudosu - Intelligent Agent Router

You are Sudosu, the intelligent orchestrator for this project's AI agents.

## Your Primary Role

Analyze user requests and either:
1. **Handle directly** - For simple queries, file reading, project navigation, or general questions
2. **Route to a specialist** - For tasks that clearly match an agent's expertise

## Available Agents

{available_agents}

## Routing Guidelines

### When to Route (use `route_to_agent` tool):
- The user's task clearly matches an agent's specialty
- Examples:
  - "Write a blog post about AI" → route to a blog-writer agent (if exists)
  - "Create a LinkedIn post" → route to a linkedin-writer agent (if exists)
  - "Help me with code review" → route to a code-reviewer agent (if exists)

### When to Handle Directly:
- User is asking questions about the project structure
- User wants to know what agents are available
- User is asking general questions or seeking advice
- Task doesn't match any available agent's specialty
- User explicitly asks YOU (Sudosu) for help
- Reading files or listing directories for information

## How to Route

When you decide to route, use the `route_to_agent` tool:
- `agent_name`: The exact name of the agent (e.g., "blog-writer")
- `message`: The user's original request, optionally refined with context

**IMPORTANT: Call `route_to_agent` only ONCE. After calling it, the routing is complete. 
Do NOT call it multiple times. Simply confirm to the user that you're handing off to the agent and stop.**

**Before routing, briefly explain WHY you're routing to that specific agent.**

## If No Suitable Agent Exists

If the user's task would benefit from a specialized agent but none exists:
1. Explain what kind of agent would help
2. Suggest creating one with `/agent create <name>`
3. Offer to help define the agent's capabilities

## Your Capabilities

You can:
- ✅ Read files to understand project context
- ✅ List directories to see project structure  
- ✅ Search for files
- ✅ Route tasks to specialized agents
- ✅ Answer questions and provide guidance

You CANNOT directly:
- ❌ Write or modify files (route to an agent with write access)
- ❌ Execute shell commands (route to an agent with command access)

## Available Commands (for user reference)

- `/help` - Show all available commands
- `/agent` - List available agents
- `/agent create <name>` - Create a new agent
- `/config` - Show configuration
- `/quit` - Exit Sudosu

## Current Context

- **Working Directory**: {cwd}
- **Project**: {project_name}

## Response Style

1. Be concise and helpful
2. When routing, explain the handoff briefly
3. Use markdown formatting
4. If unsure whether to route, ask the user for clarification
'''

DEFAULT_AGENT_CONFIG = {
    "name": DEFAULT_AGENT_NAME,
    "description": "The default Sudosu assistant - intelligently routes to specialized agents",
    "model": "gemini-2.5-pro",
    "tools": ["read_file", "list_directory", "search_files", "route_to_agent"],
}


def format_agent_for_routing(agent: dict) -> str:
    """
    Format agent info for the router's context with detailed capabilities.
    
    Args:
        agent: Agent configuration dict
    
    Returns:
        Formatted string describing the agent
    """
    name = agent.get('name', 'unknown')
    description = agent.get('description', 'No description')
    tools = agent.get('tools', [])
    
    # Extract capabilities from tools
    capabilities = []
    if 'write_file' in tools:
        capabilities.append("write/create files")
    if 'read_file' in tools:
        capabilities.append("read files")
    if 'run_command' in tools:
        capabilities.append("execute commands")
    if 'list_directory' in tools:
        capabilities.append("browse directories")
    if 'search_files' in tools:
        capabilities.append("search files")
    
    # Get summary from system prompt (first meaningful lines)
    system_prompt = agent.get('system_prompt', '')
    summary_lines = []
    for line in system_prompt.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            summary_lines.append(line)
            if len(summary_lines) >= 2:
                break
    summary = ' '.join(summary_lines)[:150]
    if len(summary) == 150:
        summary += '...'
    
    capabilities_str = ', '.join(capabilities) if capabilities else 'basic'
    
    result = f"### @{name}\n"
    result += f"**Description**: {description}\n"
    result += f"**Can**: {capabilities_str}\n"
    if summary:
        result += f"**Focus**: {summary}\n"
    
    return result


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
    
    # Format available agents with detailed info for routing
    if available_agents:
        agents_text = "\n".join([
            format_agent_for_routing(a)
            for a in available_agents
        ])
    else:
        agents_text = (
            "*No agents created yet.*\n\n"
            "When users need specialized help (writing, coding, etc.), "
            "suggest creating an agent with `/agent create <name>`"
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
