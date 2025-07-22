# MCP Server for Remote Approval

## 概要

Claude Code のリモート承認機能を実現するための MCP (Model Context Protocol) サーバーの実装検証プロジェクト。

## Phase 1: 最小限の実装

### ファイル構成

- `minimal_mcp_server.py` - 全てのリクエストを自動承認する最小限のMCPサーバー
- `claude_settings_example.json` - Claude Code設定ファイルのサンプル
- `mcp_server.log` - デバッグログファイル（実行時に生成）

### セットアップ方法

1. Claude Code の設定ファイル（`~/.claude/settings.json`）に以下を追加：

```json
{
  "mcpServers": {
    "minimal-permission": {
      "command": "uv",
      "args": ["run", "python", "mcp-server/minimal_mcp_server.py"],
      "transport": "stdio",
      "cwd": "/Users/yuya/src/github.com/yuya-takeyama/cchh"
    }
  }
}
```

2. Claude Code を再起動

### 動作確認

1. MCPサーバーが正しく起動しているか確認
2. ツール実行時の承認リクエストが自動的に処理されるか確認
3. `mcp_server.log` でログを確認

### 現在の実装状況

- [x] JSON-RPC 2.0 ベースの基本的な通信
- [x] 初期化ハンドシェイク
- [x] 権限リクエストの自動承認
- [ ] 実際のClaude Codeとの統合テスト

### 次のステップ

Phase 2 では HTTP/WebSocket ベースの実装を行い、リモートからの承認操作を可能にする。