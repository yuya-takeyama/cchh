#!/usr/bin/env python3
"""
Test script for MCP SDK server
"""

import json
import subprocess
import sys
import time
from pathlib import Path

def send_request(process, request, expect_response=True):
    """Send a JSON-RPC request to the MCP server"""
    request_str = json.dumps(request)
    print(f"\n→ Sending: {request_str}")
    process.stdin.write(request_str + "\n")
    process.stdin.flush()
    
    if expect_response:
        response = process.stdout.readline()
        if response:
            print(f"← Response: {response.strip()}")
            return json.loads(response)
    return None

def main():
    """Test the MCP SDK server"""
    print("Testing MCP SDK Server...")
    
    # Start the server
    cmd = ["uv", "run", "python", "mcp-server/mcp_server_sdk.py"]
    cwd = Path(__file__).parent.parent
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Working directory: {cwd}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=cwd
    )
    
    try:
        # Test 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        response = send_request(process, init_request)
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        send_request(process, initialized_notification, expect_response=False)
        
        # Give server time to process initialization
        time.sleep(0.5)
        
        # Test 2: List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        response = send_request(process, list_tools_request)
        
        # Test 3: Call request_approval tool
        call_tool_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "request_approval",
                "arguments": {
                    "tool_name": "bash",
                    "arguments": {"command": "rm -rf /"},
                    "session_id": "test-session"
                }
            },
            "id": 3
        }
        
        response = send_request(process, call_tool_request)
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        # Read stderr for debug logs
        process.terminate()
        stderr = process.stderr.read()
        if stderr:
            print(f"\nServer logs:\n{stderr}")

if __name__ == "__main__":
    main()