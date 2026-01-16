"""Integration command handlers for external services (Gmail, etc.)."""

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
)


# Backend URL for integration APIs
BACKEND_URL = os.environ.get("SUDOSU_BACKEND_URL", "http://localhost:8000")


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


async def check_integration_status(integration: str = "gmail") -> dict:
    """Check the status of an integration.
    
    Args:
        integration: Name of the integration (default: gmail)
        
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


async def initiate_connection(integration: str = "gmail") -> dict:
    """Initiate OAuth connection for an integration.
    
    Args:
        integration: Name of the integration (default: gmail)
        
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


async def disconnect_integration(integration: str = "gmail") -> dict:
    """Disconnect an integration.
    
    Args:
        integration: Name of the integration (default: gmail)
        
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
    """Handle /connect command - connect an integration.
    
    Usage:
        /connect gmail     - Connect Gmail account
        /connect           - Connect Gmail (default)
    """
    # Parse integration name from args
    parts = args.strip().split()
    integration = parts[0] if parts else "gmail"
    
    if integration not in ["gmail"]:
        print_error(f"Unknown integration: {integration}")
        print_info("Available integrations: gmail")
        return
    
    # Check if already connected
    print_info(f"Checking {integration} connection status...")
    status = await check_integration_status(integration)
    
    if status.get("connected"):
        print_success(f"✓ {integration.title()} is already connected!")
        if status.get("email"):
            print_info(f"  Connected as: {status['email']}")
        return
    
    # Initiate connection
    print_info(f"Initiating {integration.title()} connection...")
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
    console.print("[bold cyan]━━━ Gmail Authorization ━━━[/bold cyan]")
    console.print()
    console.print("Opening your browser to authorize Gmail access...")
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
    console.print("[yellow]Waiting for authorization...[/yellow]", end="")
    
    connected = False
    timeout = 120  # 2 minutes
    poll_interval = 2
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        console.print(".", end="", style="yellow")
        
        status = await check_integration_status(integration)
        if status.get("connected"):
            connected = True
            break
        
        await asyncio.sleep(poll_interval)
    
    console.print()  # New line after dots
    console.print()
    
    if connected:
        print_success(f"✓ {integration.title()} connected successfully!")
        if status.get("email"):
            print_info(f"  Connected as: {status['email']}")
        console.print()
        console.print("[dim]Your agent can now access Gmail. Try:[/dim]")
        console.print("[dim]  'Read my latest emails'[/dim]")
        console.print("[dim]  'Send an email to ...'[/dim]")
    else:
        print_warning("Connection timed out. Please try again with /connect gmail")


async def handle_disconnect_command(args: str = ""):
    """Handle /disconnect command - disconnect an integration.
    
    Usage:
        /disconnect gmail  - Disconnect Gmail
        /disconnect        - Disconnect Gmail (default)
    """
    # Parse integration name from args
    parts = args.strip().split()
    integration = parts[0] if parts else "gmail"
    
    if integration not in ["gmail"]:
        print_error(f"Unknown integration: {integration}")
        print_info("Available integrations: gmail")
        return
    
    # Check if connected
    status = await check_integration_status(integration)
    
    if not status.get("connected"):
        print_info(f"{integration.title()} is not connected.")
        return
    
    # Disconnect
    print_info(f"Disconnecting {integration.title()}...")
    result = await disconnect_integration(integration)
    
    if result.get("success"):
        print_success(f"✓ {integration.title()} disconnected successfully")
    else:
        print_error(f"Failed to disconnect: {result.get('error', 'Unknown error')}")


async def handle_integrations_command(args: str = ""):  # noqa: ARG001
    """Handle /integrations command - show integration status.
    
    Usage:
        /integrations      - Show status of all integrations
    """
    console.print()
    console.print("[bold cyan]━━━ Integrations ━━━[/bold cyan]")
    console.print()
    
    # Check Gmail status
    gmail_status = await check_integration_status("gmail")
    
    if gmail_status.get("connected"):
        email = gmail_status.get("email", "connected")
        console.print(f"  [green]●[/green] Gmail: [green]Connected[/green] ({email})")
    else:
        console.print("  [dim]○[/dim] Gmail: [dim]Not connected[/dim]")
    
    console.print()
    console.print("[dim]Commands:[/dim]")
    console.print("[dim]  /connect gmail     - Connect Gmail[/dim]")
    console.print("[dim]  /disconnect gmail  - Disconnect Gmail[/dim]")
    console.print()
