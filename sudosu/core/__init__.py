"""Core configuration management for Sudosu."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Default paths
GLOBAL_CONFIG_DIR = Path.home() / ".sudosu"
CONFIG_FILE = "config.yaml"

# Default backend URLs (hardcoded, not from env vars)
DEFAULT_DEV_BACKEND_URL = "ws://localhost:8000/ws"
DEFAULT_PROD_BACKEND_URL = "wss://sudosu-cli.trysudosu.com/ws"


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
            "mode": "prod",  # default to production
            "backend_url": DEFAULT_PROD_BACKEND_URL,
            "dev_backend_url": DEFAULT_DEV_BACKEND_URL,
            "prod_backend_url": DEFAULT_PROD_BACKEND_URL,
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


def get_mode() -> str:
    """Get the current mode (dev or prod)."""
    # Check environment variable first
    env_mode = os.getenv("SUDOSU_MODE", "").lower()
    if env_mode in ["dev", "prod"]:
        return env_mode
    
    # Fall back to config file
    config_mode = get_config_value("mode", "prod")
    return config_mode if config_mode in ["dev", "prod"] else "prod"


def set_mode(mode: str) -> None:
    """Set the current mode (dev or prod)."""
    if mode not in ["dev", "prod"]:
        raise ValueError("Mode must be 'dev' or 'prod'")
    set_config_value("mode", mode)
    
    # Update backend_url based on mode
    if mode == "dev":
        url = get_config_value("dev_backend_url", DEFAULT_DEV_BACKEND_URL)
    else:
        url = get_config_value("prod_backend_url", DEFAULT_PROD_BACKEND_URL)
    
    set_config_value("backend_url", url)


def get_backend_url() -> str:
    """Get the backend WebSocket URL based on current mode."""
    # Check for direct environment variable override (highest priority)
    env_url = os.getenv("SUDOSU_BACKEND_URL")
    if env_url:
        return env_url
    
    # Get current mode
    mode = get_mode()
    
    # Get mode-specific URL
    if mode == "dev":
        # Priority: env var > config file > default
        env_url = os.getenv("SUDOSU_DEV_BACKEND_URL")
        if env_url:
            return env_url
        config_url = get_config_value("dev_backend_url")
        return config_url if config_url else DEFAULT_DEV_BACKEND_URL
    else:
        # Priority: env var > config file > default
        env_url = os.getenv("SUDOSU_PROD_BACKEND_URL")
        if env_url:
            return env_url
        config_url = get_config_value("prod_backend_url")
        return config_url if config_url else DEFAULT_PROD_BACKEND_URL


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
