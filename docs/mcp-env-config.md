# MCP サーバーの環境変数設定

## 問題

MCPサーバーは独立したプロセスで起動されるため、シェルの環境変数が自動的に引き継がれません。

## 解決方法

### 方法1: Claude Code 設定ファイルで環境変数を指定

`~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cchh-remote-approval": {
      "command": "/Users/yuya/src/github.com/yuya-takeyama/cchh/mcp_server.sh",
      "args": [],
      "env": {
        "CCHH_SLACK_BOT_TOKEN": "xoxb-your-token-here",
        "CCHH_SLACK_CHANNEL_ID": "C1234567890"
      }
    }
  }
}
```

**注意**: トークンを設定ファイルに直接書くのはセキュリティ上推奨されません。

### 方法2: 環境変数を参照する（推奨）

```json
{
  "mcpServers": {
    "cchh-remote-approval": {
      "command": "/Users/yuya/src/github.com/yuya-takeyama/cchh/mcp_server.sh",
      "args": [],
      "env": {
        "CCHH_SLACK_BOT_TOKEN": "${CCHH_SLACK_BOT_TOKEN}",
        "CCHH_SLACK_CHANNEL_ID": "${CCHH_SLACK_CHANNEL_ID}"
      }
    }
  }
}
```

**注意**: この方法が Claude Code でサポートされているかは要確認。

### 方法3: シェルスクリプトで環境を読み込む

`mcp_server.sh` で `.zshrc` や `.bashrc` を source する（実装済み）。

## デバッグ方法

1. 起動ログを確認:
   ```bash
   cat ~/.cchh/logs/mcp_startup.log
   ```

2. MCPサーバーのログを確認:
   ```bash
   ls -la ~/.cchh/logs/mcp_server_*.log
   cat ~/.cchh/logs/mcp_server_*.log | tail -20
   ```

3. Slack統合のログを確認:
   ```bash
   ls -la ~/.cchh/logs/mcp_slack_*.log
   cat ~/.cchh/logs/mcp_slack_*.log | tail -20
   ```