"""Core configuration management for Sudosu."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml


# Default paths
GLOBAL_CONFIG_DIR = Path.home() / ".sudosu"
CONFIG_FILE = "config.yaml"


def get_global_config_dir() -> Path:
    """Get the global configuration directory."""
    return GLOBAL_CONFIG_DIR


def get_project_config_dir(cwd: Optional[Path] = None) -> Optional[Path]:
    """Get the project-specific configuration directory if it exists."""
    cwd = cwd or Path.cwd()
    project_config = cwd / ".sudosu"
    if project_config.exists():
        return project_config
    return None


def ensure_config_structure() -> Path:
    """
    Ensure the global config directory structure exists.
    
    NOTE: Only creates config.yaml, NOT agents directory.
    Agents are project-local only (in .sudosu/agents/).
    """
    config_dir = get_global_config_dir()
    
    # Create config directory (just for config.yaml)
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create default config if it doesn't exist
    config_file = config_dir / CONFIG_FILE
    if not config_file.exists():
        default_config = {
            "backend_url": "ws://localhost:8000/ws",
            "api_key": "",
            "default_model": "gemini-2.5-pro",
            "theme": "default",
        }
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False)
    
    return config_dir


def load_config() -> dict:
    """Load the global configuration."""
    config_file = get_global_config_dir() / CONFIG_FILE
    
    if not config_file.exists():
        return {}
    
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> None:
    """Save the global configuration."""
    config_file = get_global_config_dir() / CONFIG_FILE
    
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Set a specific configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)


def get_backend_url() -> str:
    """Get the backend WebSocket URL."""
    return get_config_value("backend_url", "ws://localhost:8000/ws")


def get_agents_dir(project_first: bool = True) -> Path:
    """Get the agents directory (project-specific or global)."""
    if project_first:
        project_dir = get_project_config_dir()
        if project_dir:
            agents_dir = project_dir / "agents"
            if agents_dir.exists():
                return agents_dir
    
    return get_global_config_dir() / "agents"


def get_skills_dir(project_first: bool = True) -> Path:
    """Get the skills directory (project-specific or global)."""
    if project_first:
        project_dir = get_project_config_dir()
        if project_dir:
            skills_dir = project_dir / "skills"
            if skills_dir.exists():
                return skills_dir
    
    return get_global_config_dir() / "skills"


# Export session management
from sudosu.core.session import (
    ConversationSession,
    SessionManager,
    get_session_manager,
    reset_session_manager,
)
