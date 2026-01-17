"""WebSocket connection manager for communicating with the backend."""

import asyncio
import json
from typing import Any, AsyncGenerator, Callable, Optional

import websockets
from websockets.client import WebSocketClientProtocol


class ConnectionManager:
    """Manages WebSocket connection to the Sudosu backend."""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.ws: Optional[WebSocketClientProtocol] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Establish connection to the backend.
        
        Timeout values increased to support long-running operations
        like bulk email fetching (100+ emails) and multi-step automations.
        """
        try:
            self.ws = await websockets.connect(
                self.backend_url,
                ping_interval=120,   # 2 minutes (was 30s)
                ping_timeout=60,     # 1 minute (was 10s)  
                max_size=20_000_000, # 20MB for large responses
            )
            self._connected = True
            return True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to backend: {e}")
    
    async def disconnect(self) -> None:
        """Close the connection."""
        if self.ws:
            await self.ws.close()
            self._connected = False
            self.ws = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to backend."""
        return self._connected and self.ws is not None
    
    async def send(self, message: dict) -> None:
        """Send a message to the backend."""
        if not self.is_connected:
            raise ConnectionError("Not connected to backend")
        
        await self.ws.send(json.dumps(message))
    
    async def receive(self) -> dict:
        """Receive a message from the backend."""
        if not self.is_connected:
            raise ConnectionError("Not connected to backend")
        
        msg = await self.ws.recv()
        return json.loads(msg)
    
    async def invoke_agent(
        self,
        agent_config: dict,
        message: str,
        cwd: str,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        on_text: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], Any]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_special_message: Optional[Callable[[dict], Any]] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Invoke an agent and stream the response with session context.
        
        Args:
            agent_config: Agent configuration dict
            message: User message
            cwd: Current working directory
            session_id: Session ID for memory continuity across agents
            thread_id: Thread ID for specific conversation continuity
            user_id: User ID for integration tools (Gmail, etc.)
            on_text: Callback for text chunks
            on_tool_call: Callback for tool calls (should return result)
            on_status: Callback for status updates
            on_special_message: Callback for special backend messages (consultation, etc.)
        
        Yields:
            Response messages from the backend
        """
        # Build request with session info for memory
        request = {
            "type": "invoke",
            "agent": agent_config,
            "message": message,
            "cwd": cwd,
        }
        
        # Include session info if provided
        if session_id:
            request["session_id"] = session_id
        if thread_id:
            request["thread_id"] = thread_id
        if user_id:
            request["user_id"] = user_id
        
        # Send invoke request
        await self.send(request)
        
        # Stream responses
        while True:
            try:
                data = await self.receive()
                msg_type = data.get("type")
                
                if msg_type == "text":
                    if on_text:
                        on_text(data.get("content", ""))
                    yield data
                
                elif msg_type == "tool_call":
                    if on_tool_call:
                        tool_name = data.get("tool")
                        tool_args = data.get("args", {})
                        
                        if on_status:
                            on_status(f"Executing {tool_name}...")
                        
                        # Execute tool and get result
                        result = await on_tool_call(tool_name, tool_args)
                        
                        # Send result back to backend
                        await self.send({
                            "type": "tool_result",
                            "tool": tool_name,
                            "result": result,
                        })
                    yield data
                
                elif msg_type == "status":
                    if on_status:
                        on_status(data.get("message", ""))
                    yield data
                
                elif msg_type == "done":
                    yield data
                    break
                
                elif msg_type == "error":
                    yield data
                    break
                
                elif msg_type == "get_available_agents":
                    # Backend is requesting available agents for consultation
                    if on_special_message:
                        response = await on_special_message(data)
                        if response:
                            await self.send(response)
                    yield data
                
                elif msg_type == "consultation_route":
                    # Backend has decided to route via consultation
                    if on_special_message:
                        await on_special_message(data)
                    yield data
                
                else:
                    yield data
                    
            except websockets.exceptions.ConnectionClosed:
                yield {"type": "error", "message": "Connection closed"}
                break
            except Exception as e:
                yield {"type": "error", "message": str(e)}
                break


async def create_connection(backend_url: str) -> ConnectionManager:
    """Create and connect to the backend."""
    manager = ConnectionManager(backend_url)
    await manager.connect()
    return manager
