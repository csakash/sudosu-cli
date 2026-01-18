"""Sudosu CLI - Your AI Coworker Platform."""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Optional

import typer

from sudosu.commands.agent import get_agent_config, get_available_agents, handle_agent_command
from sudosu.commands.config import handle_config_command
from sudosu.commands.init import init_command, init_project_command
from sudosu.commands.integrations import (
    get_user_id,
    handle_connect_command,
    handle_disconnect_command,
    handle_integrations_command,
)
from sudosu.commands.memory import handle_memory_command
from sudosu.core import ensure_config_structure, get_backend_url, get_global_config_dir
from sudosu.core.connection import ConnectionManager
from sudosu.core.default_agent import get_default_agent_config
from sudosu.core.safety import is_safe_directory, get_safety_warning
from sudosu.core.session import get_session_manager
from sudosu.tools import execute_tool
from sudosu.tools import ROUTING_MARKER
from sudosu.ui import (
    clear_screen,
    console,
    get_user_input,
    get_user_input_async,
    LiveStreamPrinter,
    print_agent_thinking,
    print_consultation_route,
    print_error,
    print_help,
    print_info,
    print_routing_to_agent,
    print_success,
    print_tool_execution,
    print_tool_result,
    print_welcome,
    StreamPrinter,
    COLOR_PRIMARY,
    COLOR_ACCENT,
)


app = typer.Typer(
    name="sudosu",
    help="Your AI Coworker Platform — AI teammates that actually get work done",
    add_completion=False,
)


def parse_agent_prompt(text: str) -> tuple[str, str]:
    """
    Parse @agent_name from the prompt.
    
    Returns:
        Tuple of (agent_name, message)
    """
    match = re.match(r"@(\w+)\s*(.*)", text, re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    return "", text


async def stream_agent_response(agent_config: dict, message: str, cwd: str, agent_name: str = "agent") -> dict | None:
    """
    Common function to stream agent response from backend with SHARED thread memory.
    
    All agents use the same thread_id to share conversation context.
    
    Returns:
        Routing info dict if agent called route_to_agent or consultation triggered routing, None otherwise
    """
    backend_url = get_backend_url()
    routing_info = None
    consultation_routing = None
    
    # Get session manager for SHARED thread memory
    session_mgr = get_session_manager()
    
    # Use shared thread_id, not per-agent thread
    thread_id = session_mgr.get_thread_id()
    session_id = session_mgr.session_id
    
    # Get user_id for integration tools (Gmail, etc.)
    user_id = get_user_id()
    
    # Increment message count
    session_mgr.increment_message_count()
    
    try:
        manager = ConnectionManager(backend_url)
        await manager.connect()
    except Exception as e:
        print_error(f"Failed to connect to backend: {e}")
        print_info("Make sure the backend is running")
        print_info(f"Backend URL: {backend_url}")
        return None
    
    try:
        stream_printer = LiveStreamPrinter()
        stream_printer.start()
        
        # Define callbacks
        def on_text(content: str):
            stream_printer.print_chunk(content)
        
        async def on_tool_call(tool_name: str, args: dict):
            nonlocal routing_info
            
            # Special handling for route_to_agent
            if tool_name == "route_to_agent":
                result = await execute_tool(tool_name, args, cwd)
                # Capture routing info for later
                if result.get(ROUTING_MARKER):
                    routing_info = {
                        "agent_name": result["agent_name"],
                        "message": result["message"],
                    }
                return result
            
            # consult_orchestrator is handled by backend - shouldn't reach here
            if tool_name == "consult_orchestrator":
                # Backend handles this, but we need to return something
                return {"output": "Consultation in progress..."}
            
            # Normal tool execution
            print_tool_execution(tool_name, args)
            result = await execute_tool(tool_name, args, cwd)
            print_tool_result(tool_name, result)
            return result
        
        def on_status(status: str):
            console.print(f"[dim]{status}[/dim]")
        
        async def on_special_message(msg: dict):
            """Handle special messages from backend."""
            nonlocal consultation_routing
            
            if msg.get("type") == "get_available_agents":
                # Backend is asking for available agents for consultation
                agents = get_available_agents()
                return {
                    "type": "available_agents",
                    "agents": agents,
                }
            
            elif msg.get("type") == "consultation_route":
                # Sub-agent consulted sudosu and got a routing decision
                consultation_routing = {
                    "from_agent": msg["from_agent"],
                    "to_agent": msg["to_agent"],
                    "reason": msg["reason"],
                    "user_request": msg["user_request"],
                }
            
            return None
        
        # Stream response with SHARED thread context for memory
        async for msg in manager.invoke_agent(
            agent_config=agent_config,
            message=message,
            cwd=cwd,
            session_id=session_id,
            thread_id=thread_id,
            user_id=user_id,
            on_text=on_text,
            on_tool_call=on_tool_call,
            on_status=on_status,
            on_special_message=on_special_message,
        ):
            if msg.get("type") == "error":
                stream_printer.flush()
                print_error(msg.get("message", "Unknown error"))
                break
            elif msg.get("type") == "done":
                stream_printer.flush()
                break
        
    finally:
        await manager.disconnect()
    
    # Check for consultation-triggered routing first
    if consultation_routing:
        return {
            "type": "consultation_route",
            **consultation_routing,
        }
    
    return routing_info


async def invoke_agent(prompt: str, cwd: str):
    """Send prompt to backend and stream response for @agent invocation."""
    # Parse @agent_name from prompt
    agent_name, message = parse_agent_prompt(prompt)
    
    if not agent_name:
        print_error("Please specify an agent: @agent_name <message>")
        return
    
    if not message:
        print_error("Please provide a message")
        return
    
    # Load agent config
    agent_config = get_agent_config(agent_name)
    
    if not agent_config:
        print_error(f"Agent '{agent_name}' not found")
        print_info("Use /agent to list available agents, or /agent create <name> to create one")
        return
    
    # Explicit @agent switches the active agent
    session_mgr = get_session_manager()
    session_mgr.set_active_agent(agent_name, via_routing=False)
    
    print_agent_thinking(agent_name)
    await stream_agent_response(agent_config, message, cwd, agent_name)


async def invoke_active_agent(message: str, cwd: str):
    """Continue conversation with the currently active agent."""
    session_mgr = get_session_manager()
    agent_name = session_mgr.get_active_agent()
    
    agent_config = get_agent_config(agent_name)
    if not agent_config:
        # Fallback to orchestrator if agent not found
        session_mgr.reset_to_orchestrator()
        await invoke_default_agent(message, cwd)
        return
    
    print_agent_thinking(agent_name)
    result = await stream_agent_response(agent_config, message, cwd, agent_name)
    
    # Handle consultation-triggered routing
    if result and result.get("type") == "consultation_route":
        target_agent = result["to_agent"]
        user_request = result["user_request"]
        reason = result["reason"]
        from_agent = result["from_agent"]
        
        # Show the consultation decision
        print_consultation_route(
            from_agent=from_agent,
            to_agent=target_agent,
            reason=reason,
        )
        
        # Load target agent and continue
        target_config = get_agent_config(target_agent)
        if target_config:
            session_mgr.set_active_agent(target_agent, via_routing=True)
            print_agent_thinking(target_agent)
            await stream_agent_response(target_config, user_request, cwd, target_agent)
        else:
            print_error(f"Agent '{target_agent}' not found")
            print_info("Available agents:")
            for agent in get_available_agents():
                console.print(f"  - @{agent['name']}")


async def invoke_default_agent(message: str, cwd: str):
    """Invoke the default Sudosu assistant with intelligent routing."""
    # Get available agents to provide context
    available_agents = get_available_agents()
    
    # Get default agent config with context
    agent_config = get_default_agent_config(available_agents, cwd)
    
    print_agent_thinking("sudosu")
    routing_info = await stream_agent_response(agent_config, message, cwd, "sudosu")
    
    # Check if the default agent decided to route to another agent
    if routing_info:
        target_agent_name = routing_info["agent_name"]
        routed_message = routing_info["message"]
        
        print_routing_to_agent(target_agent_name)
        
        # Load the target agent config
        target_config = get_agent_config(target_agent_name)
        
        if target_config:
            # Mark this agent as active for follow-ups
            session_mgr = get_session_manager()
            session_mgr.set_active_agent(target_agent_name, via_routing=True)
            
            print_agent_thinking(target_agent_name)
            await stream_agent_response(target_config, routed_message, cwd, target_agent_name)
        else:
            print_error(f"Agent '{target_agent_name}' not found")
            print_info("Available agents:")
            for agent in available_agents:
                console.print(f"  - @{agent['name']}")
            print_info("Create a new agent with /agent create <name>")


async def handle_command(command: str):
    """Handle slash commands."""
    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:]
    
    if cmd == "/help":
        print_help()
    
    elif cmd == "/agent":
        await handle_agent_command(args)
    
    elif cmd == "/config":
        await handle_config_command(args)
    
    elif cmd == "/memory":
        await handle_memory_command(args)
    
    elif cmd == "/connect":
        await handle_connect_command(" ".join(args))
    
    elif cmd == "/disconnect":
        await handle_disconnect_command(" ".join(args))
    
    elif cmd == "/integrations":
        await handle_integrations_command(" ".join(args))
    
    elif cmd == "/init":
        if args and args[0] == "project":
            init_project_command()
        else:
            await init_command()
    
    elif cmd == "/back":
        # Return from sub-agent to sudosu orchestrator
        session_mgr = get_session_manager()
        old_agent = session_mgr.get_active_agent()
        session_mgr.reset_to_orchestrator()
        if old_agent != "sudosu":
            print_info(f"Returned from @{old_agent} to sudosu")
        else:
            print_info("Already talking to sudosu")
    
    elif cmd == "/clear":
        clear_screen()
    
    elif cmd == "/quit" or cmd == "/exit":
        raise KeyboardInterrupt
    
    else:
        print_error(f"Unknown command: {cmd}")
        print_info("Type /help for available commands")


async def interactive_session():
    """Main interactive loop with active agent routing."""
    # Ensure config exists - auto-create silently if needed
    config_dir = get_global_config_dir()
    if not config_dir.exists():
        # Silent auto-init - just create config with defaults, no prompts
        await init_command(silent=True)
    
    cwd = os.getcwd()
    
    # Safety check - warn if running from unsafe directory
    is_safe, reason = is_safe_directory(Path(cwd))
    
    if not is_safe:
        console.print(get_safety_warning(reason))
        console.print("[dim]Press Enter to exit, or type 'continue' to proceed in read-only mode...[/dim]")
        response = (await get_user_input_async("")).strip().lower()
        if response != "continue":
            console.print(f"[{COLOR_ACCENT}]Exiting. Navigate to a project folder and try again.[/{COLOR_ACCENT}]")
            return
        console.print(f"[{COLOR_ACCENT}]⚠️  Running in restricted mode. Agent creation and file writes are disabled.[/{COLOR_ACCENT}]\n")
    
    # Get system username for personalized welcome
    import getpass
    username = getpass.getuser().capitalize()
    print_welcome(username)
    
    # Get session manager for active agent tracking
    session_mgr = get_session_manager()
    
    while True:
        try:
            # Show active agent in prompt
            active = session_mgr.get_active_agent()
            if active != "sudosu":
                prompt = f"[@{active}] > "
            else:
                prompt = "> "
            
            user_input = (await get_user_input_async(prompt)).strip()
            
            if not user_input:
                continue
            
            if user_input.startswith("/"):
                await handle_command(user_input)
            
            elif user_input.startswith("@"):
                # Check safety for @agent invocation
                if not is_safe:
                    print_error("Agent invocation disabled in unsafe directory")
                    print_info("Navigate to a project folder to use agents")
                    continue
                # Explicit agent switch - user is taking control
                await invoke_agent(user_input, cwd)
            
            else:
                # Plain text - route to active agent
                active_agent = session_mgr.get_active_agent()
                
                if active_agent == "sudosu":
                    # Use orchestrator - it may route to another agent
                    await invoke_default_agent(user_input, cwd)
                else:
                    # Continue with the active sub-agent
                    await invoke_active_agent(user_input, cwd)
                
        except KeyboardInterrupt:
            console.print(f"\n[{COLOR_PRIMARY}]Goodbye! 👋[/{COLOR_PRIMARY}]")
            break
        except EOFError:
            break


@app.command()
def main(
    prompt: Optional[str] = typer.Argument(None, help="Prompt to send to an agent (e.g., '@writer hello')"),
    init: bool = typer.Option(False, "--init", "-i", help="Initialize Sudosu configuration"),
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """
    Sudosu - Your AI Coworker Platform
    
    Get AI coworkers that can read your files, write code, connect to your tools
    (Gmail, Calendar, GitHub, Linear, Slack), and actually get work done.
    
    Examples:
        sudosu                          # Start interactive session
        sudosu --init                   # Initialize configuration
        sudosu "@writer write a blog"   # Direct agent invocation
    """
    if version:
        from sudosu import __version__
        console.print(f"sudosu version {__version__}")
        return
    
    if init:
        asyncio.run(init_command(silent=False))
        return
    
    if prompt:
        # Direct invocation
        cwd = os.getcwd()
        asyncio.run(invoke_agent(prompt, cwd))
    else:
        # Interactive mode
        asyncio.run(interactive_session())


if __name__ == "__main__":
    app()
