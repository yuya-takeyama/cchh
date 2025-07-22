#!/bin/bash
# MCP Server wrapper script for Claude Code

# Change to the project root directory
cd /Users/yuya/src/github.com/yuya-takeyama/cchh

# Run the MCP server with uv
exec uv run python mcp-server/mcp_server_sdk.py