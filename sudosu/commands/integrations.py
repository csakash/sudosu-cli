"""Integration command handlers for external services.

Supports: Gmail, Slack, Notion, Linear, GitHub, Google Drive, Google Docs, 
Google Sheets, and any other Composio-configured tool.
"""

import asyncio
import os
import time
import webbrowser

import httpx

from sudosu.core import get_config_value, set_config_value
from sudosu.ui import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_ACCENT,
    COLOR_INTERACTIVE,
)


# Backend URL for integration APIs
BACKEND_URL = os.environ.get("SUDOSU_BACKEND_URL", "http://localhost:8000")

# Display names for toolkits
TOOLKIT_DISPLAY_NAMES = {
    "gmail": "Gmail",
    "slack": "Slack",
    "notion": "Notion",
    "linear": "Linear",
    "github": "GitHub",
    "googledrive": "Google Drive",
    "googledocs": "Google Docs",
    "googlesheets": "Google Sheets",
}


def get_display_name(toolkit: str) -> str:
    """Get human-readable display name for a toolkit."""
    return TOOLKIT_DISPLAY_NAMES.get(toolkit, toolkit.title())


def get_user_id() -> str:
    """Get or create a unique user ID for this CLI installation.
    
    The user_id is stored in ~/.sudosu/config.yaml and is used
    to associate integrations (like Gmail) with this user.
    """
    user_id = get_config_value("user_id")
    if not user_id:
        import uuid
        user_id = str(uuid.uuid4())
        set_config_value("user_id", user_id)
    return user_id


async def get_available_integrations() -> list[dict]:
    """Get list of available integrations from backend.
    
    Returns:
        List of dicts with integration details
    """
    user_id = get_user_id()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/integrations",
                params={"user_id": user_id},
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"available": [], "connected": [], "details": []}
                
    except Exception as e:
        return {"available": [], "connected": [], "error": str(e)}


async def check_integration_status(integration: str) -> dict:
    """Check the status of any integration.
    
    Args:
        integration: Name of the integration (e.g., gmail, slack, notion)
        
    Returns:
        dict with 'connected' (bool) and other status info
    """
    user_id = get_user_id()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/integrations/{integration}/status/{user_id}",
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"connected": False, "error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def initiate_connection(integration: str) -> dict:
    """Initiate OAuth connection for any integration.
    
    Args:
        integration: Name of the integration (e.g., gmail, slack, notion)
        
    Returns:
        dict with 'auth_url' if successful, or 'error' if failed
    """
    user_id = get_user_id()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/integrations/{integration}/connect",
                json={"user_id": user_id},
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json()
                return {"error": data.get("detail", f"HTTP {response.status_code}")}
                
    except Exception as e:
        return {"error": str(e)}


async def disconnect_integration(integration: str) -> dict:
    """Disconnect any integration.
    
    Args:
        integration: Name of the integration (e.g., gmail, slack, notion)
        
    Returns:
        dict with 'success' (bool) and message
    """
    user_id = get_user_id()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/integrations/{integration}/disconnect",
                json={"user_id": user_id},
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                data = response.json()
                return {"success": False, "error": data.get("detail", f"HTTP {response.status_code}")}
                
    except Exception as e:
        return {"success": False, "error": str(e)}


async def poll_for_connection(
    integration: str = "gmail",
    timeout: int = 120,
    poll_interval: int = 2,
) -> bool:
    """Poll for connection completion after user authorizes in browser.
    
    Args:
        integration: Name of the integration
        timeout: Maximum seconds to wait
        poll_interval: Seconds between polls
        
    Returns:
        True if connected successfully, False otherwise
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = await check_integration_status(integration)
        
        if status.get("connected"):
            return True
        
        await asyncio.sleep(poll_interval)
    
    return False


async def handle_connect_command(args: str = ""):
    """Handle /connect command - connect any integration.
    
    Usage:
        /connect gmail     - Connect Gmail account
        /connect slack     - Connect Slack workspace
        /connect notion    - Connect Notion workspace
        /connect linear    - Connect Linear account
        /connect github    - Connect GitHub account
        /connect           - Show available integrations
    """
    # Get available integrations first
    integrations_info = await get_available_integrations()
    available = integrations_info.get("available", [])
    
    if "error" in integrations_info:
        print_error(f"Failed to get integrations: {integrations_info['error']}")
        print_info("Make sure the backend is running: cd sudosu-backend && uvicorn app.main:app")
        return
    
    if not available:
        print_warning("No integrations available. Configure them in your Composio account.")
        print_info("Visit: https://app.composio.dev/auth-configs")
        return
    
    # Parse integration name from args
    parts = args.strip().split()
    
    # If no integration specified, show available options
    if not parts:
        console.print()
        console.print(f"[bold {COLOR_SECONDARY}]━━━ Available Integrations ━━━[/bold {COLOR_SECONDARY}]")
        console.print()
        for toolkit in available:
            display_name = get_display_name(toolkit)
            console.print(f"  • [{COLOR_INTERACTIVE}]{toolkit}[/{COLOR_INTERACTIVE}] - {display_name}")
        console.print()
        console.print("[dim]Usage: /connect <integration>[/dim]")
        console.print("[dim]Example: /connect slack[/dim]")
        return
    
    integration = parts[0].lower()
    
    if integration not in available:
        print_error(f"Unknown integration: {integration}")
        print_info(f"Available integrations: {', '.join(available)}")
        return
    
    display_name = get_display_name(integration)
    
    # Check if already connected
    print_info(f"Checking {display_name} connection status...")
    status = await check_integration_status(integration)
    
    if status.get("connected"):
        print_success(f"✓ {display_name} is already connected!")
        return
    
    # Initiate connection
    print_info(f"Initiating {display_name} connection...")
    result = await initiate_connection(integration)
    
    if "error" in result:
        print_error(f"Failed to initiate connection: {result['error']}")
        return
    
    auth_url = result.get("auth_url")
    if not auth_url:
        print_error("No authorization URL received from backend")
        return
    
    # Open browser and wait for authorization
    console.print()
    console.print(f"[bold cyan]━━━ {display_name} Authorization ━━━[/bold cyan]")
    console.print()
    console.print(f"Opening your browser to authorize {display_name} access...")
    console.print()
    console.print("[dim]If the browser doesn't open, visit this URL:[/dim]")
    console.print(f"[link={auth_url}]{auth_url}[/link]")
    console.print()
    
    # Try to open the browser
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass  # URL already displayed above
    
    # Poll for completion
    console.print(f"[{COLOR_PRIMARY}]Waiting for authorization...[/{COLOR_PRIMARY}]", end="")
    
    connected = False
    timeout = 120  # 2 minutes
    poll_interval = 2
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        console.print(".", end="", style=COLOR_PRIMARY)
        
        status = await check_integration_status(integration)
        if status.get("connected"):
            connected = True
            break
        
        await asyncio.sleep(poll_interval)
    
    console.print()  # New line after dots
    console.print()
    
    if connected:
        print_success(f"✓ {display_name} connected successfully!")
        console.print()
        _show_integration_examples(integration)
    else:
        print_warning(f"Connection timed out. Please try again with /connect {integration}")


def _show_integration_examples(integration: str):
    """Show example commands for a connected integration."""
    examples = {
        "gmail": [
            "'Read my latest emails'",
            "'Send an email to bob@example.com'",
            "'Draft an email about the project update'",
        ],
        "slack": [
            "'Send a message to #general channel'",
            "'List my Slack channels'",
            "'Send a DM to @john'",
        ],
        "notion": [
            "'Create a new page in Notion'",
            "'Search my Notion workspace for meeting notes'",
            "'Update my project page'",
        ],
        "linear": [
            "'Create a bug issue for the login problem'",
            "'List my assigned issues'",
            "'Update issue status to In Progress'",
        ],
        "github": [
            "'Create an issue for the new feature'",
            "'List open PRs in my repo'",
            "'Star the langchain repository'",
        ],
        "googledrive": [
            "'List files in my Drive'",
            "'Upload a document'",
            "'Create a new folder'",
        ],
        "googledocs": [
            "'Create a new document'",
            "'Get content from my meeting notes doc'",
        ],
        "googlesheets": [
            "'Create a new spreadsheet'",
            "'Update values in my budget sheet'",
        ],
    }
    
    if integration in examples:
        console.print("[dim]Your agent can now:[/dim]")
        for example in examples[integration]:
            console.print(f"[dim]  {example}[/dim]")


async def handle_disconnect_command(args: str = ""):
    """Handle /disconnect command - disconnect any integration.
    
    Usage:
        /disconnect gmail  - Disconnect Gmail
        /disconnect slack  - Disconnect Slack
        /disconnect        - Show connected integrations
    """
    # Get available integrations first
    integrations_info = await get_available_integrations()
    available = integrations_info.get("available", [])
    connected = integrations_info.get("connected", [])
    
    # Parse integration name from args
    parts = args.strip().split()
    
    # If no integration specified, show connected ones
    if not parts:
        if not connected:
            print_info("No integrations are currently connected.")
            return
        
        console.print()
        console.print(f"[bold {COLOR_SECONDARY}]━━━ Connected Integrations ━━━[/bold {COLOR_SECONDARY}]")
        console.print()
        for toolkit in connected:
            display_name = get_display_name(toolkit)
            console.print(f"  • [{COLOR_INTERACTIVE}]{toolkit}[/{COLOR_INTERACTIVE}] - {display_name}")
        console.print()
        console.print("[dim]Usage: /disconnect <integration>[/dim]")
        console.print("[dim]Example: /disconnect slack[/dim]")
        return
    
    integration = parts[0].lower()
    
    if integration not in available:
        print_error(f"Unknown integration: {integration}")
        print_info(f"Available integrations: {', '.join(available)}")
        return
    
    display_name = get_display_name(integration)
    
    # Check if connected
    status = await check_integration_status(integration)
    
    if not status.get("connected"):
        print_info(f"{display_name} is not connected.")
        return
    
    # Disconnect
    print_info(f"Disconnecting {display_name}...")
    result = await disconnect_integration(integration)
    
    if result.get("success") or result.get("connected") is False:
        print_success(f"✓ {display_name} disconnected successfully")
    else:
        print_error(f"Failed to disconnect: {result.get('error', 'Unknown error')}")


async def get_registry_info() -> dict:
    """Get tool registry information from backend.
    
    Returns:
        Dict with registry data or error
    """
    user_id = get_user_id()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/registry/{user_id}/summary",
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        return {"error": str(e)}


async def handle_integrations_command(args: str = ""):  # noqa: ARG001
    """Handle /integrations command - show all integration status.
    
    Usage:
        /integrations      - Show status of all integrations
    """
    console.print()
    console.print("[bold cyan]━━━ Integrations ━━━[/bold cyan]")
    console.print()
    
    # Get all integrations with status
    integrations_info = await get_available_integrations()
    
    if "error" in integrations_info:
        print_error(f"Failed to get integrations: {integrations_info['error']}")
        print_info("Make sure the backend is running.")
        return
    
    details = integrations_info.get("details", [])
    available = integrations_info.get("available", [])
    
    if not details and not available:
        print_warning("No integrations configured.")
        print_info("Configure integrations at: https://app.composio.dev/auth-configs")
        return
    
    # Show status for each integration
    if details:
        for item in details:
            slug = item.get("slug", "")
            name = item.get("name", slug.title())
            is_connected = item.get("connected", False)
            
            if is_connected:
                console.print(f"  [{COLOR_INTERACTIVE}]●[/{COLOR_INTERACTIVE}] {name}: [{COLOR_INTERACTIVE}]Connected[/{COLOR_INTERACTIVE}]")
            else:
                console.print(f"  [dim]○[/dim] {name}: [dim]Not connected[/dim]")
    else:
        # Fallback: check each available integration
        for toolkit in available:
            display_name = get_display_name(toolkit)
            status = await check_integration_status(toolkit)
            
            if status.get("connected"):
                console.print(f"  [{COLOR_INTERACTIVE}]●[/{COLOR_INTERACTIVE}] {display_name}: [{COLOR_INTERACTIVE}]Connected[/{COLOR_INTERACTIVE}]")
            else:
                console.print(f"  [dim]○[/dim] {display_name}: [dim]Not connected[/dim]")
    
    # Show tool registry info
    console.print()
    console.print(f"[bold {COLOR_SECONDARY}]━━━ Tool Registry ━━━[/bold {COLOR_SECONDARY}]")
    console.print()
    
    registry_info = await get_registry_info()
    
    if "error" in registry_info:
        console.print(f"  [dim]Registry not available: {registry_info['error']}[/dim]")
    else:
        connected_count = registry_info.get("connected_count", 0)
        connected = registry_info.get("connected", [])
        
        if connected_count == 0:
            console.print("  [dim]No tools registered (connect an integration first)[/dim]")
        else:
            console.print(f"  [dim]Smart tool loading enabled[/dim]")
            for item in connected:
                slug = item.get("slug", "")
                display_name = item.get("display_name", slug.title())
                tool_count = item.get("tool_count", 0)
                capabilities = item.get("capabilities", [])[:3]
                
                console.print(f"  • [{COLOR_INTERACTIVE}]{display_name}[/{COLOR_INTERACTIVE}]: {tool_count} tools")
                if capabilities:
                    caps_str = ", ".join(capabilities[:3])
                    console.print(f"    [dim]Capabilities: {caps_str}[/dim]")
    
    console.print()
    console.print("[dim]Commands:[/dim]")
    console.print("[dim]  /connect <integration>     - Connect an integration[/dim]")
    console.print("[dim]  /disconnect <integration>  - Disconnect an integration[/dim]")
    console.print()
    console.print("[dim]Examples:[/dim]")
    console.print("[dim]  /connect slack[/dim]")
    console.print("[dim]  /connect notion[/dim]")
    console.print("[dim]  /disconnect gmail[/dim]")
    console.print()
