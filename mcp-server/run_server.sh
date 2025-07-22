#!/bin/bash
# エラーログファイル
ERROR_LOG="/Users/yuya/src/github.com/yuya-takeyama/cchh/mcp-server/startup_error.log"

# エラー出力をログファイルにも記録
exec 2> >(tee -a "$ERROR_LOG" >&2)

echo "[$(date)] Starting MCP server wrapper..." >&2
echo "[$(date)] PATH=$PATH" >&2

cd /Users/yuya/src/github.com/yuya-takeyama/cchh || exit 1
echo "[$(date)] Changed to directory: $(pwd)" >&2

# uvのフルパスを使用
UV_PATH="/Users/yuya/.local/share/aquaproj-aqua/bin/uv"
if [ -x "$UV_PATH" ]; then
    echo "[$(date)] Using uv at: $UV_PATH" >&2
    exec "$UV_PATH" run python mcp-server/minimal_mcp_server.py
else
    echo "[$(date)] ERROR: uv not found at $UV_PATH" >&2
    exit 1
fi