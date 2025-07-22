# Claude Code リモート承認システム実装計画

## 実装対象
GitHub Issue #16: Claude Code リモート承認システム「ゴロ寝コンピューティング」エクスペリエンスの実現

## 実装フェーズ

### フェーズ 1: MCP サーバーの基本実装（現在のターゲット）

#### 1.1 MCP サーバーのセットアップ
- [x] `mcp` パッケージのインストール（pyproject.toml に追加）
- [x] `src/mcp/` ディレクトリの作成
- [x] `src/mcp/server.py` で基本的な MCP サーバーを実装
- [x] `approval_prompt` ツールの実装

#### 1.2 承認リクエスト待受サーバーの実装
- [x] `src/mcp/approval_server.py` で HTTP サーバーを実装
- [x] `/approve` エンドポイント（POST）で承認を受け付け
- [x] `/deny` エンドポイント（POST）で拒否を受け付け
- [x] 承認待ちキューの管理（メモリ内で OK）
- [x] タイムアウト処理（デフォルト 5 分）

#### 1.3 MCP サーバー起動スクリプト
- [x] `mcp_server.py` または `mcp_server.sh` の作成
- [x] stdio トランスポートでの JSON-RPC 通信対応
- [ ] エラーハンドリングとログ出力

#### 1.4 動作確認
- [ ] Claude Code に MCP サーバーを登録
- [ ] `--permission-prompt-tool` オプションで起動
- [x] curl での承認/拒否テスト（基本動作確認済み）
- [x] タイムアウトの動作確認（10秒でタイムアウト確認済み）

### フェーズ 2: Slack 統合（後日実装）
- Slack アプリのインタラクティブボタン対応
- 既存の cchh Slack 通知との統合
- ずんだもんボイス「許可が欲しいのだ」の実装

### フェーズ 3: 実用性向上（後日実装）
- コマンドリスクレベル判定
- 承認履歴のロギング
- エラー時の音声通知

## 技術仕様

### MCP サーバー実装

```python
# src/mcp/server.py
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types

server = Server("cchh-remote-approval")

@server.tool()
async def approval_prompt(
    tool_name: str,
    input: dict[str, Any],
    tool_use_id: str | None = None,
) -> types.TextContent:
    """
    リモートで承認を待機する
    """
    # 1. 承認リクエストを作成
    # 2. HTTP サーバーに登録
    # 3. 承認/拒否を待機（タイムアウトあり）
    # 4. 結果を返す
    pass
```

### 承認待受サーバー

```python
# src/mcp/approval_server.py
from aiohttp import web
import asyncio
from typing import Dict, Optional

class ApprovalServer:
    def __init__(self):
        self.pending_approvals: Dict[str, asyncio.Future] = {}
    
    async def create_approval_request(self, request_id: str, details: dict):
        """承認リクエストを作成して待機"""
        future = asyncio.Future()
        self.pending_approvals[request_id] = future
        
        # タイムアウト設定
        asyncio.create_task(self._timeout_handler(request_id))
        
        return await future
    
    async def approve(self, request_id: str):
        """承認処理"""
        if request_id in self.pending_approvals:
            self.pending_approvals[request_id].set_result({"behavior": "allow"})
    
    async def deny(self, request_id: str):
        """拒否処理"""
        if request_id in self.pending_approvals:
            self.pending_approvals[request_id].set_result({"behavior": "deny"})
```

### 設定ファイル

```bash
# .claude/mcp/cchh-remote-approval.json
{
  "name": "cchh-remote-approval",
  "command": "cd /path/to/cchh && uv run python mcp_server.py",
  "args": [],
  "env": {}
}
```

## curl での動作確認手順

```bash
# 1. MCP サーバーを起動
claude mcp add cchh-remote-approval /path/to/cchh/mcp_server.sh

# 2. Claude Code を起動
claude-code --permission-prompt-tool cchh-remote-approval

# 3. 承認が必要なコマンドを実行
# （別ターミナルで）

# 4. 承認リクエストの確認
curl http://localhost:8080/pending

# 5. 承認を送信
curl -X POST http://localhost:8080/approve -d '{"request_id": "xxx"}'

# 6. または拒否を送信
curl -X POST http://localhost:8080/deny -d '{"request_id": "xxx"}'
```

## 作業進捗

### 2025-01-23
- GitHub Issue #16 の内容を確認
- 実装計画を作成（このファイル）
- 作業ブランチ `yuya-takeyama/feat/remote-approval` を作成
- `mcp` と `aiohttp` パッケージを pyproject.toml に追加
- MCP サーバーの基本実装を完了:
  - `src/mcp/server.py`: MCP サーバー本体
  - `src/mcp/approval_server.py`: HTTP 承認待受サーバー
  - `mcp_server.sh`: 起動スクリプト
- 実装した機能:
  - `approval_prompt` ツールの実装
  - HTTP エンドポイント (`/pending`, `/approve`, `/deny`, `/health`)
  - タイムアウト処理（5分）
  - 承認待ちキューの管理

## 今回の成果

✅ **MCP サーバーの基本実装完了！**
- `approval_prompt` ツールが正常に動作
- HTTP サーバーでの承認待受機能を実装
- タイムアウトによる自動拒否機能も確認
- localhost での curl テスト完了

## 次のステップ
1. Claude Code に MCP サーバーを登録
2. `--permission-prompt-tool` オプションで実際の動作確認
3. エラーハンドリングとログ出力の改善
4. Slack 統合の実装（フェーズ 2）