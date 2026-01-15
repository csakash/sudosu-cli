"""Config command handler."""

from sudosu.core import load_config, set_config_value
from sudosu.ui import console, print_error, print_info, print_success


def show_config():
    """Show current configuration."""
    config = load_config()
    
    console.print("\n[bold]Current Configuration:[/bold]\n")
    
    for key, value in config.items():
        # Mask API key
        if "key" in key.lower() and value:
            display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
        else:
            display_value = value
        
        console.print(f"  [cyan]{key}[/cyan]: {display_value}")
    
    console.print()


def set_config(key: str, value: str):
    """Set a configuration value."""
    valid_keys = ["backend_url", "api_key", "default_model", "theme"]
    
    if key not in valid_keys:
        print_error(f"Invalid key: {key}")
        print_info(f"Valid keys: {', '.join(valid_keys)}")
        return
    
    set_config_value(key, value)
    
    # Mask display for sensitive values
    if "key" in key.lower():
        display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
    else:
        display_value = value
    
    print_success(f"Set {key} = {display_value}")


async def handle_config_command(args: list[str]):
    """Handle /config command with subcommands."""
    if not args:
        show_config()
        return
    
    if args[0] == "set":
        if len(args) < 3:
            print_error("Usage: /config set <key> <value>")
            return
        set_config(args[1], " ".join(args[2:]))
    else:
        print_error(f"Unknown subcommand: {args[0]}")
        print_info("Usage: /config or /config set <key> <value>")
