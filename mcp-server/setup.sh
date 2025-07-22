#!/bin/bash
# MCPサーバーをClaude Codeに登録するスクリプト

# プロジェクトのルートディレクトリを取得
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "MCPサーバーをClaude Codeに登録します..."
echo "プロジェクトルート: ${PROJECT_ROOT}"

# 既存の登録を削除（存在する場合）
claude mcp remove minimal-permission 2>/dev/null || true

# MCPサーバーを登録（ローカルスコープ）
# cwdを含めた完全なコマンドラインを指定
claude mcp add minimal-permission "cd ${PROJECT_ROOT} && uv run python mcp-server/minimal_mcp_server.py"

echo ""
echo "✅ MCPサーバーを登録しました。"
echo ""
echo "登録されたサーバーを確認:"
claude mcp list | grep minimal-permission || echo "（登録が表示されない場合は、コマンドを再実行してください）"