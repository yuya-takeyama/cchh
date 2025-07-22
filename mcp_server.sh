#!/bin/bash

# MCP server startup script for cchh-remote-approval

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the MCP server
exec uv run python -m src.mcp.server