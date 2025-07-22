#!/bin/bash

# MCP server startup script for cchh-remote-approval

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Debug: Log environment variables
mkdir -p ~/.cchh/logs
echo "[DEBUG] Starting MCP server at $(date)" >> ~/.cchh/logs/mcp_startup.log
echo "[DEBUG] CCHH_SLACK_BOT_TOKEN: ${CCHH_SLACK_BOT_TOKEN:+SET}" >> ~/.cchh/logs/mcp_startup.log
echo "[DEBUG] CCHH_SLACK_CHANNEL_ID: ${CCHH_SLACK_CHANNEL_ID:+SET}" >> ~/.cchh/logs/mcp_startup.log

# Source the user's shell profile to get environment variables
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
elif [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Run the MCP server
exec uv run python -m src.mcp.server