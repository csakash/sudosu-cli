"""Agent loader - Parse and load AGENT.md files."""

from pathlib import Path
from typing import Any, Optional

import frontmatter

from sudosu.core.default_agent import CONTEXT_AWARE_PROMPT, SUB_AGENT_CONSULTATION_PROMPT


def parse_agent_file(agent_path: Path) -> Optional[dict]:
    """
    Parse an AGENT.md file and return the agent configuration.
    
    Args:
        agent_path: Path to the agent directory containing AGENT.md
    
    Returns:
        Agent configuration dict or None if invalid
    """
    agent_md = agent_path / "AGENT.md"
    
    if not agent_md.exists():
        return None
    
    try:
        with open(agent_md, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        
        # Get description - ensure it's a string
        description = post.get("description", "")
        if isinstance(description, list):
            description = "\n".join(str(item) for item in description)
        
        # Get tools list
        tools = post.get("tools", ["read_file", "write_file", "list_directory"])
        if isinstance(tools, str):
            tools = [tools]
        
        # Get the base system prompt and append context-aware instructions
        base_prompt = str(post.content).strip()
        # Append context awareness to all agents for better conversation handling
        # Also append consultation instructions so sub-agents know when to consult sudosu
        system_prompt = base_prompt + CONTEXT_AWARE_PROMPT + SUB_AGENT_CONSULTATION_PROMPT
        
        return {
            "name": str(post.get("name", agent_path.name)),
            "description": str(description),
            "model": str(post.get("model", "gemini-2.5-pro")),
            "tools": tools,
            "skills": post.get("skills", []),
            "system_prompt": system_prompt,
            "path": str(agent_path),
        }
    except Exception as e:
        print(f"Error parsing agent file {agent_md}: {e}")
        return None


def discover_agents(agents_dir: Path) -> list[dict]:
    """
    Discover all agents in a directory.
    
    Args:
        agents_dir: Path to the agents directory
    
    Returns:
        List of agent configurations
    """
    agents = []
    
    if not agents_dir.exists():
        return agents
    
    for item in agents_dir.iterdir():
        if item.is_dir():
            agent = parse_agent_file(item)
            if agent:
                agents.append(agent)
    
    return agents


def load_agent_config(agent_name: str, agents_dirs: list[Path]) -> Optional[dict]:
    """
    Load a specific agent's configuration by name.
    
    Args:
        agent_name: Name of the agent to load
        agents_dirs: List of directories to search for agents
    
    Returns:
        Agent configuration dict or None if not found
    """
    for agents_dir in agents_dirs:
        agent_path = agents_dir / agent_name
        if agent_path.exists():
            return parse_agent_file(agent_path)
    
    return None


def create_agent_template(
    agent_dir: Path,
    name: str,
    description: str,
    system_prompt: str,
    model: str = "gemini-2.5-pro",
    tools: Optional[list[str]] = None,
) -> Path:
    """
    Create a new agent from a template.
    
    Args:
        agent_dir: Directory where the agent will be created
        name: Agent name
        description: Agent description
        system_prompt: Agent system prompt (markdown body)
        model: Model to use
        tools: List of allowed tools
    
    Returns:
        Path to the created agent directory
    """
    if tools is None:
        tools = ["read_file", "write_file", "list_directory"]
    
    # Create agent directory
    agent_path = agent_dir / name
    agent_path.mkdir(parents=True, exist_ok=True)
    
    # Create AGENT.md
    agent_md = agent_path / "AGENT.md"
    
    content = f"""---
name: {name}
description: {description}
model: {model}
tools:
{chr(10).join(f'  - {tool}' for tool in tools)}
skills: []
---

{system_prompt}
"""
    
    with open(agent_md, "w", encoding="utf-8") as f:
        f.write(content)
    
    return agent_path


DEFAULT_WRITER_PROMPT = """# Writer Agent

You are a professional content writer. You help users create well-structured, 
engaging content including blog posts, articles, and documentation.

## IMPORTANT: Always Save Your Work

**You MUST always save your written content to a file using the write_file tool.**
- Use kebab-case for filenames (e.g., `my-blog-post.md`)
- Always use the `.md` extension for blog posts and articles
- Save the file AFTER you finish writing the content

## Guidelines

1. If the request is clear, start writing immediately
2. Structure content with clear headings and sections
3. Use proper markdown formatting
4. **Always save the final content to a .md file**

## Writing Style

- Clear and concise
- Engaging but professional
- Well-researched (when applicable)
- SEO-friendly for blog posts

## Workflow

1. Write the full content in markdown format
2. **ALWAYS use write_file to save the content** - this is mandatory
3. After saving, give a BRIEF confirmation (1-2 sentences max)

## CRITICAL: After Saving a File

**After the write_file tool succeeds, you MUST:**
- Give a SHORT confirmation like "✓ Saved to filename.md"
- Optionally add ONE brief insight or suggestion
- **DO NOT repeat or summarize the content you just saved**
- **DO NOT show the content again**
- **Keep your response after saving to 2-3 sentences maximum**

Example good response after saving:
"✓ Saved your blog post to ai-revolution.md. The article covers 5 key areas where AI is transforming CS. Let me know if you'd like any revisions!"

Example BAD response (DO NOT DO THIS):
"Here is the blog post about AI... [repeating the entire content]"
"""


DEFAULT_CODER_PROMPT = """# Coder Agent

You are an expert software developer. You help users write, review, and debug code
across various programming languages and frameworks.

## Guidelines

1. Understand the project context before making changes
2. Follow existing code style and conventions
3. Write clean, well-documented code
4. Consider edge cases and error handling

## Best Practices

- Use meaningful variable and function names
- Add comments for complex logic
- Follow SOLID principles
- Write testable code

## Output Format

When writing code:
1. Explain the approach first
2. Show the code with proper formatting
3. Explain any important decisions
4. Save files with appropriate names and extensions
"""


AGENT_TEMPLATES = {
    "writer": {
        "description": "A helpful writing assistant that creates blog posts, articles, and documentation.",
        "system_prompt": DEFAULT_WRITER_PROMPT,
    },
    "coder": {
        "description": "An expert developer that helps write, review, and debug code.",
        "system_prompt": DEFAULT_CODER_PROMPT,
    },
}
