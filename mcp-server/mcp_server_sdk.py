#!/usr/bin/env python3
"""
MCP Server implementation using FastMCP SDK for remote approval functionality
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel

# デバッグ用ログディレクトリの設定
LOG_DIR = Path(os.path.expanduser("~/.cchh/mcp_logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# FastMCPサーバーのインスタンス作成
server = FastMCP(
    name="cchh-remote-approval",
    instructions="Remote approval handler for Claude Code Hook Handlers (CCHH)",
    debug=True,
    log_level="DEBUG"
)

# 承認リクエストのデータモデル
class ApprovalRequest(BaseModel):
    id: str
    tool: str
    arguments: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None

# 承認待ちリクエストを保存する辞書（実際の実装ではDBやRedisを使用）
pending_approvals: Dict[str, ApprovalRequest] = {}

@server.tool()
async def request_approval(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: Optional[str] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Request approval for a tool execution
    
    Args:
        tool_name: Name of the tool requiring approval
        arguments: Tool arguments
        session_id: Claude session ID
        ctx: MCP context for logging
    
    Returns:
        Approval response with status and details
    """
    request_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # 承認リクエストを作成
    approval_request = ApprovalRequest(
        id=request_id,
        tool=tool_name,
        arguments=arguments,
        timestamp=datetime.now().isoformat(),
        session_id=session_id
    )
    
    # リクエストを保存
    pending_approvals[request_id] = approval_request
    
    if ctx:
        await ctx.info(f"Approval requested for tool: {tool_name}")
        await ctx.report_progress(0, 100, "Waiting for approval...")
    
    logger.info(f"Approval request created: {request_id} for tool: {tool_name}")
    logger.debug(f"Arguments: {json.dumps(arguments, indent=2)}")
    
    # TODO: ここで実際の承認待ち処理を実装
    # 現在は自動承認のみ
    await asyncio.sleep(1)  # シミュレーション
    
    response = {
        "approved": True,
        "request_id": request_id,
        "tool": tool_name,
        "message": "Auto-approved (remote approval not yet implemented)",
        "timestamp": datetime.now().isoformat()
    }
    
    if ctx:
        await ctx.report_progress(100, 100, "Approved!")
    
    logger.info(f"Approval response: {json.dumps(response, indent=2)}")
    return response

@server.tool()
async def list_pending_approvals(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    List all pending approval requests
    
    Returns:
        List of pending approval requests
    """
    if ctx:
        await ctx.info(f"Listing {len(pending_approvals)} pending approvals")
    
    return {
        "count": len(pending_approvals),
        "approvals": [
            {
                "id": req.id,
                "tool": req.tool,
                "timestamp": req.timestamp,
                "session_id": req.session_id
            }
            for req in pending_approvals.values()
        ]
    }

@server.tool()
async def approve_request(
    request_id: str,
    approved: bool = True,
    reason: Optional[str] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Approve or reject a pending request
    
    Args:
        request_id: ID of the approval request
        approved: Whether to approve or reject
        reason: Optional reason for the decision
    
    Returns:
        Approval decision details
    """
    if request_id not in pending_approvals:
        return {
            "error": f"Request ID not found: {request_id}",
            "status": "not_found"
        }
    
    request = pending_approvals.pop(request_id)
    
    if ctx:
        status = "approved" if approved else "rejected"
        await ctx.info(f"Request {request_id} {status}")
    
    return {
        "request_id": request_id,
        "tool": request.tool,
        "approved": approved,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }

# リソース定義（承認履歴など）
@server.resource("approval://history")
async def get_approval_history() -> str:
    """Get approval history (placeholder)"""
    return json.dumps({
        "message": "Approval history not yet implemented",
        "timestamp": datetime.now().isoformat()
    })

@server.tool()
async def approval_prompt(
    tool_name: str,
    input: Dict[str, Any],
    tool_use_id: Optional[str] = None,
    ctx: Optional[Context] = None
) -> str:
    """
    Permission prompt tool for Claude Code SDK
    Simulates approval - approves if input contains 'allow', otherwise denies
    
    Args:
        tool_name: The name of the tool requesting permission
        input: The input for the tool
        tool_use_id: The unique tool use request ID
    
    Returns:
        JSON-stringified approval/denial response
    """
    logger.info(f"Permission prompt for tool: {tool_name}, tool_use_id: {tool_use_id}")
    logger.debug(f"Input: {json.dumps(input, indent=2)}")
    
    # TODO: ここでリモート承認のロジックを実装
    # 現在はデモ用に 'allow' が含まれていれば承認
    input_str = json.dumps(input)
    
    if "allow" in input_str.lower():
        result = {
            "behavior": "allow",
            "updatedInput": input
        }
        logger.info("Permission ALLOWED")
    else:
        result = {
            "behavior": "deny", 
            "message": "Permission denied by cchh-remote-approval"
        }
        logger.info("Permission DENIED")
    
    # JSON文字列化して返す（ドキュメントの要件）
    return json.dumps(result)

# プロンプト定義（承認リクエストのフォーマット）
@server.prompt()
async def format_approval_request(tool_name: str, arguments: Dict[str, Any]) -> list[dict]:
    """Format an approval request for display"""
    return [{
        "role": "user",
        "content": f"""
## Tool Approval Request

**Tool**: {tool_name}
**Arguments**: 
```json
{json.dumps(arguments, indent=2)}
```

Please review and approve/reject this tool execution.
"""
    }]

def main():
    """Main entry point"""
    logger.info("Starting CCHH Remote Approval MCP Server")
    logger.info(f"Log directory: {LOG_DIR}")
    
    # stdio transportで起動
    server.run(transport="stdio")

if __name__ == "__main__":
    main()