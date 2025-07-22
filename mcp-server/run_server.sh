#!/bin/bash
# エラーログファイル
ERROR_LOG="/Users/yuya/src/github.com/yuya-takeyama/cchh/mcp-server/startup_error.log"

# エラー出力をログファイルにも記録
exec 2> >(tee -a "$ERROR_LOG" >&2)

echo "[$(date)] Starting MCP server wrapper..." >&2
cd /Users/yuya/src/github.com/yuya-takeyama/cchh || exit 1
echo "[$(date)] Changed to directory: $(pwd)" >&2

# uvが使えるか確認
which uv >&2 || echo "[$(date)] WARNING: uv not found in PATH" >&2

exec uv run python mcp-server/minimal_mcp_server.py