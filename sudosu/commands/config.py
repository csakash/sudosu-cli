"""Config command handler."""

from sudosu.core import load_config, set_config_value, get_mode, set_mode, get_backend_url
from sudosu.ui import (
    console,
    print_error,
    print_info,
    print_success,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_INTERACTIVE,
)


def show_config():
    """Show current configuration."""
    config = load_config()
    current_mode = get_mode()
    current_url = get_backend_url()
    
    console.print("\n[bold]Current Configuration:[/bold]\n")
    
    # Show mode first
    console.print(f"  [{COLOR_INTERACTIVE}]mode[/{COLOR_INTERACTIVE}]: [bold]{current_mode}[/bold] (active)")
    console.print(f"  [{COLOR_INTERACTIVE}]active_backend_url[/{COLOR_INTERACTIVE}]: {current_url}\n")
    
    for key, value in config.items():
        # Mask API key
        if "key" in key.lower() and value:
            display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
        else:
            display_value = value
        
        console.print(f"  [{COLOR_INTERACTIVE}]{key}[/{COLOR_INTERACTIVE}]: {display_value}")
    
    console.print()
    console.print("[dim]Tip: Use '/config mode dev' or '/config mode prod' to switch environments[/dim]\n")


def set_config(key: str, value: str):
    """Set a configuration value."""
    valid_keys = ["backend_url", "dev_backend_url", "prod_backend_url", "api_key", "default_model", "theme"]
    
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


def switch_mode(mode: str):
    """Switch between dev and prod modes."""
    mode = mode.lower()
    if mode not in ["dev", "prod"]:
        print_error("Mode must be 'dev' or 'prod'")
        return
    
    try:
        set_mode(mode)
        new_url = get_backend_url()
        print_success(f"Switched to {mode.upper()} mode")
        print_info(f"Backend URL: {new_url}")
    except Exception as e:
        print_error(f"Failed to switch mode: {e}")


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
    elif args[0] == "mode":
        if len(args) < 2:
            current_mode = get_mode()
            print_info(f"Current mode: {current_mode.upper()}")
            print_info("Usage: /config mode <dev|prod>")
            return
        switch_mode(args[1])
    else:
        print_error(f"Unknown subcommand: {args[0]}")
        print_info("Usage: /config or /config set <key> <value> or /config mode <dev|prod>")
