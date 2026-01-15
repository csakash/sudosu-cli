"""Session management for conversation continuity with SHARED thread model.

This module tracks conversation sessions to enable memory continuity
with the backend. All agents in a session share the SAME thread_id,
enabling seamless handoffs where sub-agents see the full conversation
context.

Key concepts:
- session_id: Unique ID for this CLI instance
- thread_id: SAME as session_id (shared across all agents)
- active_agent: The agent currently handling the conversation
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationSession:
    """Tracks a SHARED conversation session across all agents."""
    
    session_id: str
    thread_id: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    message_count: int = 0
    active_agent: str = "sudosu"
    is_routed: bool = False
    
    def touch(self):
        """Update last activity and increment message count."""
        self.last_activity = time.time()
        self.message_count += 1
    
    @property
    def duration_seconds(self) -> float:
        """Get the duration of this conversation in seconds."""
        return self.last_activity - self.created_at
    
    @property
    def is_active(self) -> bool:
        """Check if conversation has been active recently (within 30 minutes)."""
        return (time.time() - self.last_activity) < 1800


class SessionManager:
    """Manages conversation sessions with SHARED thread model.
    
    Key concepts:
    - session_id: Unique ID for this CLI instance
    - thread_id: SAME as session_id (shared across all agents)
    - active_agent: The agent currently handling the conversation
    
    All agents share the same conversation thread, enabling seamless
    handoffs where sub-agents see the full context of what was discussed
    with the orchestrator.
    """
    
    def __init__(self):
        """Initialize session manager with unique session ID."""
        # Unique ID for this CLI session
        self.session_id = str(uuid.uuid4())
        # SHARED THREAD: Single thread for the entire session
        self.thread_id = self.session_id
        # Track which agent is currently active
        self.active_agent: str = "sudosu"  # Default to orchestrator
        # Track if we're in a routed conversation
        self.is_routed: bool = False
        # Message count for the shared conversation
        self.message_count: int = 0
        # Session creation time
        self.created_at: float = time.time()
        # Last activity time
        self.last_activity: float = time.time()
    
    def get_thread_id(self) -> str:
        """Get the shared thread ID for this session.
        
        All agents use the same thread_id to share conversation history.
        """
        return self.thread_id
    
    def set_active_agent(self, agent_name: str, via_routing: bool = False):
        """Set the currently active agent.
        
        Args:
            agent_name: Name of the agent now handling the conversation
            via_routing: True if this was set via routing from sudosu
        """
        self.active_agent = agent_name
        self.is_routed = via_routing
    
    def get_active_agent(self) -> str:
        """Get the currently active agent."""
        return self.active_agent or "sudosu"
    
    def reset_to_orchestrator(self):
        """Reset back to the default sudosu orchestrator."""
        self.active_agent = "sudosu"
        self.is_routed = False
    
    def increment_message_count(self):
        """Increment the shared message count and update activity."""
        self.message_count += 1
        self.last_activity = time.time()
    
    def clear_session(self) -> str:
        """Clear the session by generating a new thread_id.
        
        This starts a fresh conversation for all agents while keeping
        the same session_id.
        
        Returns:
            New thread_id for the fresh conversation
        """
        # Create new thread with unique suffix to start fresh
        self.thread_id = f"{self.session_id}:{uuid.uuid4().hex[:8]}"
        self.message_count = 0
        self.active_agent = "sudosu"
        self.is_routed = False
        self.last_activity = time.time()
        return self.thread_id
    
    def get_stats(self) -> dict:
        """Get statistics about current session.
        
        Returns:
            Dict with session statistics
        """
        duration = time.time() - self.created_at
        return {
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "active_agent": self.active_agent,
            "is_routed": self.is_routed,
            "message_count": self.message_count,
            "duration_seconds": duration,
        }
    
    # Legacy compatibility methods
    def get_or_create_conversation(self, agent_name: str) -> "SessionManager":
        """Legacy method - returns self since we use shared thread.
        
        This maintains compatibility with existing code that expects
        a conversation object.
        """
        # Update active agent tracking
        self.set_active_agent(agent_name)
        return self
    
    def clear_conversation(self, agent_name: str) -> Optional[str]:
        """Clear the shared conversation.
        
        Since all agents share the same thread, this clears everything.
        The agent_name is kept for backward compatibility.
        """
        return self.clear_session()
    
    def clear_all_conversations(self) -> int:
        """Clear the shared conversation.
        
        Returns 1 since there's only one shared conversation.
        """
        self.clear_session()
        return 1
    
    def get_active_conversation(self) -> Optional["SessionManager"]:
        """Get the current session (self) for compatibility."""
        return self if self.message_count > 0 else None
    
    @property
    def conversations(self) -> dict:
        """Legacy property - returns dict with self if active."""
        if self.message_count > 0:
            return {self.active_agent: self}
        return {}
    
    @property
    def agent_name(self) -> str:
        """Legacy property for compatibility."""
        return self.active_agent


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager.
    
    Returns:
        The global SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def reset_session_manager():
    """Reset the global session manager (useful for testing)."""
    global _session_manager
    _session_manager = None
