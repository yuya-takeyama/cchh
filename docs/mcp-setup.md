# MCP サーバーのセットアップ方法

## 1. Claude Code 設定ファイルを開く

```bash
# macOS/Linux の場合
~/.claude/claude_desktop_config.json

# または
~/.config/claude/claude_desktop_config.json
```

## 2. MCP サーバーを登録

設定ファイルに以下を追加：

```json
{
  "mcpServers": {
    "cchh-remote-approval": {
      "command": "/Users/yuya/src/github.com/yuya-takeyama/cchh/mcp_server.sh",
      "args": [],
      "env": {}
    }
  }
}
```

**注意**: パスは絶対パスで指定する必要があります！

## 3. Claude Code を再起動

設定を反映させるために Claude Code を再起動します。

## 4. MCP サーバーの動作確認

Claude Code で以下のコマンドを実行：

```bash
# MCP サーバーが認識されているか確認
# （Claude Code の UI で確認できるはず）
```

## 5. リモート承認機能を有効化して起動

```bash
claude-code --permission-prompt-tool cchh-remote-approval
```

これで、コマンド実行時の承認が MCP サーバー経由で行われるようになります！

## 動作の流れ

1. Claude Code がコマンドを実行しようとする
2. `approval_prompt` ツールが呼ばれる
3. HTTP サーバー（localhost:8080）で承認待ち
4. 別ターミナルで curl で承認/拒否
5. 結果が Claude Code に返される

## トラブルシューティング

### MCP サーバーが起動しない場合

1. スクリプトの実行権限を確認：
   ```bash
   chmod +x /Users/yuya/src/github.com/yuya-takeyama/cchh/mcp_server.sh
   ```

2. Python 環境を確認：
   ```bash
   cd /Users/yuya/src/github.com/yuya-takeyama/cchh
   uv run python -m src.mcp.server
   ```

3. ログを確認：
   - Claude Code のログ
   - MCP サーバーの標準エラー出力

### 承認リクエストが来ない場合

1. `--permission-prompt-tool` オプションを忘れていないか確認
2. MCP サーバーが正しく登録されているか確認
3. HTTP サーバーが localhost:8080 で起動しているか確認