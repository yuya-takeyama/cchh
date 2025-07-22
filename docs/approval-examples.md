# 承認操作の実例

## 基本的な承認フロー

### 1. Claude Code でコマンドを実行
```bash
# Claude Code で危険なコマンドを実行しようとする
rm -rf /important/directory
```

### 2. 承認待ちリクエストが発生
MCP サーバーが承認リクエストを作成し、HTTP サーバーで待機

### 3. 別ターミナルで pending 確認
```bash
# pending リクエストを確認
curl http://localhost:8080/pending | jq
```

出力例：
```json
{
  "pending": [
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "tool_name": "bash",
      "input": {
        "command": "rm -rf /important/directory"
      },
      "tool_use_id": "tool-12345"
    }
  ]
}
```

### 4. 承認または拒否

#### 承認する場合（危険を理解した上で）
```bash
curl -X POST http://localhost:8080/approve \
  -H "Content-Type: application/json" \
  -d '{"request_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

#### 拒否する場合（安全を優先）
```bash
curl -X POST http://localhost:8080/deny \
  -H "Content-Type: application/json" \
  -d '{"request_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

## 便利なワンライナー

### 最初の pending を承認
```bash
curl http://localhost:8080/pending -s | \
  jq -r '.pending[0].request_id' | \
  xargs -I {} curl -X POST http://localhost:8080/approve \
    -H "Content-Type: application/json" \
    -d '{"request_id": "{}"}'
```

### 最初の pending を拒否
```bash
curl http://localhost:8080/pending -s | \
  jq -r '.pending[0].request_id' | \
  xargs -I {} curl -X POST http://localhost:8080/deny \
    -H "Content-Type: application/json" \
    -d '{"request_id": "{}"}'
```

## タイムアウトについて

- デフォルトは 5 分（300 秒）
- タイムアウトすると自動的に拒否（deny）される
- 安全のための仕組み

## ヘルスチェック

サーバーが動いているか確認：
```bash
curl http://localhost:8080/health
```

レスポンス：
```json
{"status": "ok"}
```