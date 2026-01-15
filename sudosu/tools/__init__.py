"""Local tool execution for Sudosu client."""

import fnmatch
import os
import subprocess
from pathlib import Path
from typing import Any


# Special routing result marker
ROUTING_MARKER = "_sudosu_routing"

# Special consultation routing marker
CONSULTATION_ROUTING_MARKER = "_sudosu_consultation_route"


async def execute_tool(tool_name: str, args: dict, cwd: str) -> dict:
    """
    Execute a tool locally and return the result.
    
    Args:
        tool_name: Name of the tool to execute
        args: Tool arguments
        cwd: Current working directory
    
    Returns:
        Tool execution result
    """
    executors = {
        "write_file": tool_write_file,
        "read_file": tool_read_file,
        "list_directory": tool_list_directory,
        "run_command": tool_run_command,
        "search_files": tool_search_files,
        "route_to_agent": tool_route_to_agent,
        "consult_orchestrator": tool_consult_orchestrator,
    }
    
    executor = executors.get(tool_name)
    if not executor:
        return {"error": f"Unknown tool: {tool_name}"}
    
    return await executor(args, cwd)


async def tool_consult_orchestrator(args: dict, cwd: str) -> dict:  # noqa: ARG001
    """
    Handle consultation with the orchestrator.
    
    Note: This is a stub - actual consultation is handled by the backend.
    The backend intercepts this tool call and evaluates the consultation
    before returning a decision.
    
    Args:
        args: {"situation": str, "user_request": str}
        cwd: Current working directory (unused)
    
    Returns:
        Consultation result (handled by backend)
    """
    # This should not be reached - backend handles this tool
    return {
        "output": "Consultation handled by backend",
    }


async def tool_route_to_agent(args: dict, cwd: str) -> dict:  # noqa: ARG001
    """
    Handle routing to another agent.
    
    This returns a special marker that the CLI intercepts to perform
    the actual agent handoff.
    
    Args:
        args: {"agent_name": str, "message": str}
        cwd: Current working directory (unused for routing)
    
    Returns:
        Special routing result with marker
    """
    agent_name = args.get("agent_name")
    message = args.get("message", "")
    
    if not agent_name:
        return {"error": "Missing 'agent_name' argument"}
    
    # Return special routing marker that CLI will intercept
    # The output message must clearly indicate completion to prevent
    # the LLM from calling route_to_agent again in a loop
    return {
        ROUTING_MARKER: True,
        "agent_name": agent_name,
        "message": message,
        "output": f"SUCCESS: Request has been routed to @{agent_name}. The handoff is complete. Do not call route_to_agent again. Simply confirm the routing to the user and stop.",
    }


def _validate_path(path: str, cwd: str) -> tuple[bool, str, Path]:
    """
    Validate that a path is within the allowed directory.
    
    Returns:
        Tuple of (is_valid, error_message, resolved_path)
    """
    try:
        cwd_path = Path(cwd).resolve()
        full_path = (cwd_path / path).resolve()
        
        # Check if path is within cwd
        full_path.relative_to(cwd_path)
        
        return True, "", full_path
    except ValueError:
        return False, "Path must be within current directory", Path()
    except Exception as e:
        return False, str(e), Path()


async def tool_write_file(args: dict, cwd: str) -> dict:
    """
    Write content to a file.
    
    Args:
        args: {"file_path": str or "path": str, "content": str}
        cwd: Current working directory
    
    Returns:
        Result dict with success status
    """
    # Support both file_path (backend) and path (legacy) naming
    path = args.get("file_path") or args.get("path")
    content = args.get("content")
    
    if not path:
        return {"error": "Missing 'path' argument"}
    if content is None:
        return {"error": "Missing 'content' argument"}
    
    # Validate path
    is_valid, error, full_path = _validate_path(path, cwd)
    if not is_valid:
        return {"error": error}
    
    try:
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {
            "success": True,
            "path": str(full_path),
            "message": f"File written successfully: {path}",
            "output": f"File written successfully: {path}",
        }
    except PermissionError:
        return {"error": f"Permission denied: {path}", "output": f"Error: Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to write file: {e}", "output": f"Error: Failed to write file: {e}"}


async def tool_read_file(args: dict, cwd: str) -> dict:
    """
    Read content from a file.
    
    Args:
        args: {"file_path": str or "path": str}
        cwd: Current working directory
    
    Returns:
        Result dict with file content
    """
    # Support both file_path (backend) and path (legacy) naming
    path = args.get("file_path") or args.get("path")
    
    if not path:
        return {"error": "Missing 'path' argument"}
    
    # Validate path
    is_valid, error, full_path = _validate_path(path, cwd)
    if not is_valid:
        return {"error": error}
    
    if not full_path.exists():
        return {"error": f"File not found: {path}"}
    
    if not full_path.is_file():
        return {"error": f"Not a file: {path}"}
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "path": str(full_path),
            "output": content,
        }
    except PermissionError:
        return {"error": f"Permission denied: {path}", "output": f"Error: Permission denied: {path}"}
    except UnicodeDecodeError:
        return {"error": f"Cannot read file (binary?): {path}", "output": f"Error: Cannot read file (binary?): {path}"}
    except Exception as e:
        return {"error": f"Failed to read file: {e}", "output": f"Error: Failed to read file: {e}"}


async def tool_list_directory(args: dict, cwd: str) -> dict:
    """
    List directory contents.
    
    Args:
        args: {"directory_path": str or "path": str} (optional, defaults to ".")
        cwd: Current working directory
    
    Returns:
        Result dict with directory listing
    """
    # Support both directory_path (backend) and path (legacy) naming
    path = args.get("directory_path") or args.get("path", ".")
    
    # Validate path
    is_valid, error, full_path = _validate_path(path, cwd)
    if not is_valid:
        return {"error": error}
    
    if not full_path.exists():
        return {"error": f"Directory not found: {path}"}
    
    if not full_path.is_dir():
        return {"error": f"Not a directory: {path}"}
    
    try:
        items = []
        for item in sorted(full_path.iterdir()):
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        
        # Format output as a listing
        output_lines = []
        for item in items:
            prefix = "[DIR]" if item["type"] == "dir" else "[FILE]"
            output_lines.append(f"{prefix} {item['name']}")
        
        return {
            "success": True,
            "path": str(full_path),
            "items": items,
            "output": "\n".join(output_lines) if output_lines else "Empty directory",
        }
    except PermissionError:
        return {"error": f"Permission denied: {path}", "output": f"Error: Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to list directory: {e}", "output": f"Error: Failed to list directory: {e}"}


async def tool_run_command(args: dict, cwd: str) -> dict:
    """
    Run a shell command (with restrictions).
    
    Args:
        args: {"command": str}
        cwd: Current working directory
    
    Returns:
        Result dict with command output
    """
    command = args.get("command")
    
    if not command:
        return {"error": "Missing 'command' argument"}
    
    # Restricted commands for safety
    blocked_patterns = [
        "rm -rf /",
        "sudo",
        "> /dev/",
        "mkfs",
        "dd if=",
    ]
    
    for pattern in blocked_patterns:
        if pattern in command:
            return {
                "error": f"Command blocked for safety: contains '{pattern}'",
                "output": f"Error: Command blocked for safety: contains '{pattern}'",
            }
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
            check=False,
        )
        
        # Combine stdout and stderr for output
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "output": output.strip() if output else "(no output)",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (60s limit)", "output": "Error: Command timed out (60s limit)"}
    except Exception as e:
        return {"error": f"Failed to run command: {e}", "output": f"Error: Failed to run command: {e}"}


async def tool_search_files(args: dict, cwd: str) -> dict:
    """
    Search for files matching a pattern.
    
    Args:
        args: {"pattern": str, "directory": str (optional)}
        cwd: Current working directory
    
    Returns:
        Result dict with matching files
    """
    pattern = args.get("pattern")
    directory = args.get("directory", ".")
    
    if not pattern:
        return {"error": "Missing 'pattern' argument"}
    
    # Validate path
    is_valid, error, full_path = _validate_path(directory, cwd)
    if not is_valid:
        return {"error": error}
    
    if not full_path.exists():
        return {"error": f"Directory not found: {directory}"}
    
    if not full_path.is_dir():
        return {"error": f"Not a directory: {directory}"}
    
    try:
        matches = []
        # Use glob for ** patterns, fnmatch for simple patterns
        if "**" in pattern:
            for match in full_path.glob(pattern):
                matches.append(str(match.relative_to(full_path)))
        else:
            for root, dirs, files in os.walk(full_path):
                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        rel_path = os.path.relpath(os.path.join(root, filename), full_path)
                        matches.append(rel_path)
        
        return {
            "success": True,
            "matches": matches,
            "count": len(matches),
            "output": "\n".join(matches) if matches else "No matches found",
        }
    except PermissionError:
        return {"error": f"Permission denied: {directory}"}
    except OSError as e:
        return {"error": f"Failed to search: {e}"}
