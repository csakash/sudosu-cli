"""Memory/conversation management commands.

This module provides CLI commands for viewing and managing
conversation memory and session state with SHARED thread model.

All agents share the same conversation context, so clearing
memory affects all agents.
"""

from sudosu.core.session import get_session_manager
from sudosu.ui import (
    console,
    print_success,
    print_info,
    print_error,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_ACCENT,
    COLOR_INTERACTIVE,
)


async def handle_memory_command(args: list[str]):
    """
    Handle /memory commands for SHARED conversation memory management.
    
    Usage:
        /memory           - Show current session info
        /memory clear     - Clear conversation (all agents share it)
        /memory show      - Show conversation summary
        /memory stats     - Show session statistics
        /memory agent     - Show which agent is currently active
    
    Args:
        args: Command arguments
    """
    session_mgr = get_session_manager()
    
    if not args:
        # Show session info
        _show_session_info(session_mgr)
        return
    
    cmd = args[0].lower()
    
    if cmd == "clear":
        await _handle_clear(session_mgr)
    elif cmd == "show":
        _show_conversation_details(session_mgr)
    elif cmd == "stats":
        _show_stats(session_mgr)
    elif cmd == "agent":
        _show_active_agent(session_mgr)
    elif cmd == "help":
        _show_help()
    else:
        print_error(f"Unknown memory command: {cmd}")
        _show_help()


def _show_session_info(session_mgr):
    """Display current session information."""
    console.print(f"\n[bold {COLOR_SECONDARY}]📝 Session Info[/bold {COLOR_SECONDARY}]")
    console.print(f"  Session ID: [dim]{session_mgr.session_id[:8]}...[/dim]")
    console.print(f"  Thread ID: [dim]{session_mgr.thread_id[:16]}...[/dim]")
    console.print(f"  Active Agent: [{COLOR_INTERACTIVE}]@{session_mgr.get_active_agent()}[/{COLOR_INTERACTIVE}]")
    console.print(f"  Messages: [{COLOR_PRIMARY}]{session_mgr.message_count}[/{COLOR_PRIMARY}]")
    
    if session_mgr.is_routed:
        console.print(f"  Status: [{COLOR_INTERACTIVE}]Routed from sudosu[/{COLOR_INTERACTIVE}]")
    
    console.print()
    console.print("[dim]💡 All agents share the same conversation context.[/dim]")
    console.print("[dim]   Use '/back' to return to sudosu from a sub-agent.[/dim]")
    console.print()


async def _handle_clear(session_mgr):
    """Handle memory clear command."""
    # With shared thread, there's only one conversation to clear
    new_thread_id = session_mgr.clear_session()
    print_success("Conversation cleared - starting fresh")
    console.print(f"[dim]New thread: {new_thread_id[:16]}...[/dim]")
    console.print("[dim]All agents will start fresh on next message.[/dim]")


def _show_conversation_details(session_mgr):
    """Show detailed information about the shared conversation."""
    if session_mgr.message_count > 0:
        console.print(f"\n[bold {COLOR_SECONDARY}]💬 Shared Conversation[/bold {COLOR_SECONDARY}]")
        console.print(f"  Active Agent: [{COLOR_INTERACTIVE}]@{session_mgr.get_active_agent()}[/{COLOR_INTERACTIVE}]")
        console.print(f"  Messages exchanged: [{COLOR_PRIMARY}]{session_mgr.message_count}[/{COLOR_PRIMARY}]")
        console.print(f"  Thread ID: [dim]{session_mgr.thread_id}[/dim]")
        console.print(f"  Session ID: [dim]{session_mgr.session_id}[/dim]")
        
        stats = session_mgr.get_stats()
        duration = stats["duration_seconds"]
        if duration < 60:
            console.print(f"  Duration: {duration:.0f} seconds")
        elif duration < 3600:
            console.print(f"  Duration: {duration/60:.1f} minutes")
        else:
            console.print(f"  Duration: {duration/3600:.1f} hours")
        
        if session_mgr.is_routed:
            console.print(f"\n[dim]You were routed here by sudosu.[/dim]")
            console.print("[dim]Use '/back' to return to sudosu.[/dim]")
        else:
            console.print(f"\n[dim]All agents share this conversation context.[/dim]")
        console.print("[dim]Use '/memory clear' to start fresh.[/dim]\n")
    else:
        print_info("No active conversation")
        console.print("[dim]Start chatting with an agent to see conversation details.[/dim]")


def _show_active_agent(session_mgr):
    """Show which agent is currently active."""
    active = session_mgr.get_active_agent()
    console.print(f"\nActive agent: [{COLOR_INTERACTIVE}]@{active}[/{COLOR_INTERACTIVE}]")
    
    if session_mgr.is_routed:
        console.print("[dim]You were routed here by sudosu.[/dim]")
        console.print("[dim]Use /back to return to sudosu.[/dim]")
    elif active != "sudosu":
        console.print(f"[dim]You switched to this agent with @{active}.[/dim]")
        console.print("[dim]Use /back to return to sudosu.[/dim]")
    else:
        console.print("[dim]Sudosu is the default orchestrator.[/dim]")
        console.print("[dim]It can route you to specialized agents.[/dim]")
    console.print()


def _show_stats(session_mgr):
    """Show session statistics."""
    stats = session_mgr.get_stats()
    
    console.print(f"\n[bold {COLOR_SECONDARY}]📊 Session Statistics[/bold {COLOR_SECONDARY}]")
    console.print(f"  Session ID: [dim]{stats['session_id'][:8]}...[/dim]")
    console.print(f"  Thread ID: [dim]{stats['thread_id'][:16]}...[/dim]")
    console.print(f"  Active Agent: [{COLOR_INTERACTIVE}]@{stats['active_agent']}[/{COLOR_INTERACTIVE}]")
    console.print(f"  Total Messages: [{COLOR_PRIMARY}]{stats['message_count']}[/{COLOR_PRIMARY}]")
    
    duration = stats["duration_seconds"]
    if duration < 60:
        console.print(f"  Session Duration: {duration:.0f} seconds")
    elif duration < 3600:
        console.print(f"  Session Duration: {duration/60:.1f} minutes")
    else:
        console.print(f"  Session Duration: {duration/3600:.1f} hours")
    
    if stats["is_routed"]:
        console.print(f"  Status: [{COLOR_INTERACTIVE}]Routed conversation[/{COLOR_INTERACTIVE}]")
    
    console.print()


def _show_help():
    """Show memory command help."""
    console.print(f"\n[bold {COLOR_SECONDARY}]Memory Commands[/bold {COLOR_SECONDARY}]")
    console.print(f"  [{COLOR_INTERACTIVE}]/memory[/{COLOR_INTERACTIVE}]        - Show session info and conversation status")
    console.print(f"  [{COLOR_INTERACTIVE}]/memory show[/{COLOR_INTERACTIVE}]   - Show detailed conversation info")
    console.print(f"  [{COLOR_INTERACTIVE}]/memory clear[/{COLOR_INTERACTIVE}]  - Clear conversation and start fresh")
    console.print(f"  [{COLOR_INTERACTIVE}]/memory agent[/{COLOR_INTERACTIVE}]  - Show which agent is currently active")
    console.print(f"  [{COLOR_INTERACTIVE}]/memory stats[/{COLOR_INTERACTIVE}]  - Show session statistics")
    console.print(f"  [{COLOR_INTERACTIVE}]/memory help[/{COLOR_INTERACTIVE}]   - Show this help")
    console.print()
    console.print("[dim]💡 All agents share the same conversation context.")
    console.print("   When sudosu routes you to a sub-agent, follow-up")
    console.print("   messages go to that agent until you use /back.[/dim]")
    console.print()
