"""First-time user onboarding flow.

This module handles the onboarding experience for new Sudosu users,
collecting profile information to personalize the agent experience.
"""

from typing import Optional

import httpx
from prompt_toolkit import PromptSession

from sudosu.commands.integrations import get_http_backend_url, get_user_id
from sudosu.core import get_config_value, set_config_value
from sudosu.ui import (
    console,
    print_info,
    print_success,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_INTERACTIVE,
)


# Role options for selection
ROLE_OPTIONS = [
    ("developer", "Developer / Engineer"),
    ("pm", "Product Manager"),
    ("designer", "Designer"),
    ("founder", "Founder / Entrepreneur"),
    ("marketer", "Marketer"),
    ("writer", "Writer / Content Creator"),
    ("student", "Student"),
    ("other", "Other"),
]


def is_onboarding_completed() -> bool:
    """Check if user has completed onboarding."""
    return get_config_value("onboarding_completed", False)


def mark_onboarding_completed():
    """Mark onboarding as completed."""
    set_config_value("onboarding_completed", True)


async def check_remote_profile() -> Optional[dict]:
    """Check if user profile exists on backend.
    
    This enables cross-device sync - if a user completes onboarding
    on one device, they won't need to do it again on another.
    
    Returns:
        User profile dict if found, None otherwise
    """
    user_id = get_user_id()
    backend_url = get_http_backend_url()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{backend_url}/api/users/{user_id}")
            if response.status_code == 200:
                return response.json()
    except Exception:  # noqa: BLE001
        # Silently fail - we'll just run onboarding locally
        pass
    return None


async def save_profile_to_backend(profile: dict) -> bool:
    """Save user profile to backend database.
    
    Args:
        profile: User profile dictionary
        
    Returns:
        True if saved successfully, False otherwise
    """
    backend_url = get_http_backend_url()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{backend_url}/api/users/",
                json=profile,
            )
            return response.status_code == 200
    except Exception:  # noqa: BLE001
        # Silently fail - profile is still saved locally
        return False


async def run_onboarding() -> dict:
    """Run the interactive onboarding flow.
    
    Asks the user a series of questions to personalize their experience.
    
    Returns:
        User profile dict
    """
    console.print()
    console.print(f"[bold {COLOR_PRIMARY}]--- Welcome to Sudosu! ---[/bold {COLOR_PRIMARY}]")
    console.print()
    console.print(f"[{COLOR_SECONDARY}]Let's personalize your experience with a few quick questions.[/{COLOR_SECONDARY}]")
    console.print("[dim](This only takes 30 seconds)[/dim]")
    console.print()
    
    profile = {"user_id": get_user_id()}
    session = PromptSession()
    
    # Question 1: Name
    console.print(f"[bold {COLOR_INTERACTIVE}]What should I call you?[/bold {COLOR_INTERACTIVE}]")
    try:
        name = await session.prompt_async("Your name: ")
        profile["name"] = name.strip() or "Friend"
    except (EOFError, KeyboardInterrupt):
        profile["name"] = "Friend"
    console.print()
    
    # Question 2: Email
    console.print(f"[bold {COLOR_INTERACTIVE}]What's your email?[/bold {COLOR_INTERACTIVE}]")
    console.print("[dim]We'll use this to identify your account[/dim]")
    try:
        email = await session.prompt_async("Your email: ")
        email = email.strip()
        # Basic email validation
        if email and "@" in email and "." in email:
            profile["email"] = email
        else:
            if email:
                console.print("[dim]Invalid email format, skipping...[/dim]")
            profile["email"] = None
    except (EOFError, KeyboardInterrupt):
        profile["email"] = None
    console.print()
    
    # Question 3: Role (with selection)
    console.print(f"[bold {COLOR_INTERACTIVE}]What's your role?[/bold {COLOR_INTERACTIVE}]")
    console.print("[dim]Pick the closest match:[/dim]")
    for i, (_, label) in enumerate(ROLE_OPTIONS, 1):
        console.print(f"  [{COLOR_INTERACTIVE}]{i}[/{COLOR_INTERACTIVE}]. {label}")
    
    try:
        role_input = await session.prompt_async("Enter number (or type custom): ")
        try:
            role_idx = int(role_input.strip()) - 1
            if 0 <= role_idx < len(ROLE_OPTIONS):
                profile["role"] = ROLE_OPTIONS[role_idx][0]
            else:
                profile["role"] = role_input.strip() or None
        except ValueError:
            profile["role"] = role_input.strip() or None
    except (EOFError, KeyboardInterrupt):
        profile["role"] = None
    console.print()
    
    # Question 4: Work context
    console.print(f"[bold {COLOR_INTERACTIVE}]What do you mainly work on?[/bold {COLOR_INTERACTIVE}]")
    console.print("[dim]e.g., 'Building a SaaS product', 'Mobile apps', 'Content marketing'[/dim]")
    try:
        work_context = await session.prompt_async("Your work: ")
        profile["work_context"] = work_context.strip() or None
    except (EOFError, KeyboardInterrupt):
        profile["work_context"] = None
    console.print()
    
    # Question 5: Goals
    console.print(f"[bold {COLOR_INTERACTIVE}]What do you want to accomplish with Sudosu?[/bold {COLOR_INTERACTIVE}]")
    console.print("[dim]e.g., 'Automate repetitive tasks', 'Write better content', 'Ship faster'[/dim]")
    try:
        goals = await session.prompt_async("Your goals: ")
        profile["goals"] = goals.strip() or None
    except (EOFError, KeyboardInterrupt):
        profile["goals"] = None
    console.print()
    
    # Question 6: Daily tools (optional)
    console.print(f"[bold {COLOR_INTERACTIVE}]Any tools you use daily?[/bold {COLOR_INTERACTIVE}] [dim](optional)[/dim]")
    console.print("[dim]e.g., 'github, slack, notion' (comma-separated)[/dim]")
    try:
        tools_input = await session.prompt_async("Tools (or press Enter to skip): ")
        if tools_input.strip():
            profile["daily_tools"] = [t.strip().lower() for t in tools_input.split(",") if t.strip()]
        else:
            profile["daily_tools"] = []
    except (EOFError, KeyboardInterrupt):
        profile["daily_tools"] = []
    
    console.print()
    
    # Save locally first (always works)
    set_config_value("user_profile", profile)
    
    # Try to save to backend (may fail if offline)
    console.print(f"[{COLOR_SECONDARY}]Saving your profile...[/{COLOR_SECONDARY}]")
    saved_remote = await save_profile_to_backend(profile)
    
    if saved_remote:
        print_success("Profile saved!")
    else:
        print_info("Profile saved locally (will sync when online)")
    
    # Mark completed
    mark_onboarding_completed()
    
    # Personalized welcome
    console.print()
    console.print(f"[bold {COLOR_PRIMARY}]--- All set, {profile['name']}! ---[/bold {COLOR_PRIMARY}]")
    console.print()
    console.print(f"[{COLOR_SECONDARY}]I'll remember your preferences and tailor my suggestions.[/{COLOR_SECONDARY}]")
    
    # Show relevant integration suggestions based on daily tools
    if profile.get("daily_tools"):
        supported_tools = ["gmail", "github", "slack", "notion", "linear", "googledrive", "googledocs"]
        suggested = [t for t in profile["daily_tools"] if t in supported_tools]
        if suggested:
            console.print()
            console.print(f"[dim]Tip: Connect your tools with /connect {suggested[0]}[/dim]")
    
    console.print()
    
    return profile


async def ensure_onboarding() -> Optional[dict]:
    """Ensure onboarding is completed. Returns user profile if available.
    
    This is called at the start of interactive_session() in cli.py.
    It handles three scenarios:
    1. Onboarding already completed locally -> return cached profile
    2. User exists on backend (cross-device) -> sync and return profile
    3. New user -> run onboarding flow
    
    Returns:
        User profile dict, or None if onboarding was skipped
    """
    # Check local flag first (fastest path)
    if is_onboarding_completed():
        return get_config_value("user_profile")
    
    # Check if profile exists on backend (returning user on new device)
    remote_profile = await check_remote_profile()
    if remote_profile and remote_profile.get("onboarding_completed"):
        # Cache locally and mark complete
        set_config_value("user_profile", remote_profile)
        mark_onboarding_completed()
        name = remote_profile.get("name", "Friend")
        console.print(f"[{COLOR_SECONDARY}]Welcome back, {name}![/{COLOR_SECONDARY}]")
        console.print()
        return remote_profile
    
    # Run onboarding for new users
    return await run_onboarding()


def get_user_profile() -> Optional[dict]:
    """Get the cached user profile.
    
    Returns:
        User profile dict, or None if not set
    """
    return get_config_value("user_profile")


async def handle_profile_command(args: str = ""):
    """Handle /profile command - view or update profile.
    
    Usage:
        /profile        - View current profile
        /profile edit   - Re-run onboarding to update profile
    """
    parts = args.strip().split()
    
    if parts and parts[0] == "edit":
        # Re-run onboarding
        await run_onboarding()
        return
    
    # Show current profile
    profile = get_user_profile()
    
    if not profile:
        print_info("No profile found. Run /profile edit to set up.")
        return
    
    console.print()
    console.print(f"[bold {COLOR_SECONDARY}]--- Your Profile ---[/bold {COLOR_SECONDARY}]")
    console.print()
    console.print(f"  [bold]Name:[/bold] {profile.get('name', 'Not set')}")
    console.print(f"  [bold]Email:[/bold] {profile.get('email', 'Not set')}")
    console.print(f"  [bold]Role:[/bold] {profile.get('role', 'Not set')}")
    console.print(f"  [bold]Work:[/bold] {profile.get('work_context', 'Not set')}")
    console.print(f"  [bold]Goals:[/bold] {profile.get('goals', 'Not set')}")
    
    tools = profile.get("daily_tools", [])
    if tools:
        console.print(f"  [bold]Tools:[/bold] {', '.join(tools)}")
    
    console.print()
    console.print("[dim]Run /profile edit to update[/dim]")
    console.print()


async def sync_profile_to_backend():
    """Sync local profile to backend if not already synced.
    
    Called opportunistically when backend becomes available.
    """
    profile = get_user_profile()
    if not profile:
        return
    
    # Check if already on backend
    remote = await check_remote_profile()
    if remote:
        return  # Already synced
    
    # Try to save
    await save_profile_to_backend(profile)
