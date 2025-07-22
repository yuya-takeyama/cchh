"""MCP server for remote approval."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from .approval_server import ApprovalServer
from .slack_integration import SlackIntegration

# Set up logging to file
log_dir = Path.home() / ".cchh" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_debug(message: str):
    """Write debug log to file."""
    with open(log_file, "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

# Create server instance
server = Server("cchh-remote-approval")

# Create approval server instance
approval_server = ApprovalServer()

# Create Slack integration instance
slack_integration = SlackIntegration()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="approval_prompt",
            description="Request remote approval for a command",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool requesting approval",
                    },
                    "input": {
                        "type": "object",
                        "description": "Input parameters for the tool",
                    },
                    "tool_use_id": {
                        "type": ["string", "null"],
                        "description": "ID of the tool use",
                    },
                },
                "required": ["tool_name", "input"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    # Debug logging
    log_debug(f"Tool called: {name}")
    log_debug(f"Arguments: {json.dumps(arguments)}")
    
    if name != "approval_prompt":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments:
        raise ValueError("Missing arguments")

    tool_name = arguments.get("tool_name")
    input_data = arguments.get("input", {})
    tool_use_id = arguments.get("tool_use_id")

    if not tool_name:
        raise ValueError("Missing tool_name")

    # Create approval request
    request_id = str(uuid.uuid4())
    details = {
        "tool_name": tool_name,
        "input": input_data,
        "tool_use_id": tool_use_id,
    }

    # Try to get session ID from various sources
    # 1. From tool input (if Claude Code passes it)
    session_id = input_data.get("session_id", "")
    
    # 2. If not in input, try environment variable
    if not session_id:
        import os
        session_id = os.environ.get("CCHH_CLAUDE_SESSION_ID", "")
    
    log_debug(f"Session ID: {session_id}")
    log_debug(f"Slack configured: {slack_integration.is_configured}")

    # Send Slack notification if configured
    if session_id and slack_integration.is_configured:
        asyncio.create_task(
            asyncio.to_thread(
                slack_integration.send_approval_request,
                session_id,
                request_id,
                tool_name,
                input_data,
            )
        )

    # Wait for approval (with timeout)
    try:
        result = await approval_server.create_approval_request(
            request_id, details, session_id
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    except asyncio.TimeoutError:
        # Timeout - auto deny
        result = {"behavior": "deny"}
        return [types.TextContent(type="text", text=json.dumps(result))]


async def run():
    """Run the MCP server."""
    log_debug("MCP server starting...")
    log_debug(f"Log file: {log_file}")
    
    # Start approval HTTP server in background
    await approval_server.start()
    log_debug(f"HTTP approval server started on port {approval_server.port}")

    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cchh-remote-approval",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run())