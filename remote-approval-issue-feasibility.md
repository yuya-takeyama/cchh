# Claude Code リモート承認機能 実現性検証計画

## 検証の目的

Custom Permission Prompt Tool を使用したリモート承認機能が実際に動作するかを最小限のステップで確認する。

## 検証ステップ

### Phase 1: 最小限のMCPサーバー実装（1-2時間）

#### 1.1 stdio ベースの単純なMCPサーバー作成
```python
# minimal_mcp_server.py
# 全てのリクエストを自動承認する最小実装
```

**検証項目:**
- Claude Code から MCP サーバーが認識されるか
- 基本的な通信が成立するか
- Permission Prompt のリクエストを受信できるか

#### 1.2 Claude Code 設定への登録
```json
{
  "mcpServers": {
    "test-permission": {
      "command": "python",
      "args": ["minimal_mcp_server.py"]
    }
  }
}
```

**成功基準:**
- MCP サーバーが起動する
- Claude Code のログにエラーが出ない

### Phase 2: HTTP/WebSocket 実装（2-3時間）

#### 2.1 HTTPサーバーでの実装
```python
# http_mcp_server.py
# Flask/FastAPI を使用した HTTP エンドポイント実装
```

**検証項目:**
- リモート通信が可能か
- レスポンス形式が正しく処理されるか

#### 2.2 基本的な承認フロー実装
- 承認待ちキューの実装
- シンプルなWeb UIでの承認ボタン

**成功基準:**
- ブラウザから承認操作ができる
- Claude Code が承認を待って処理を継続する

### Phase 3: 実用性の検証（1-2時間）

#### 3.1 Slack 連携のプロトタイプ
```python
# slack_approval_bot.py
# 既存の CCHH と連携して承認ボタンを表示
```

**検証項目:**
- モバイルから承認可能か
- レスポンス時間は実用的か
- エラー処理は適切か

### Phase 4: 検証結果のまとめ（30分）

#### 4.1 動作確認チェックリスト
- [ ] MCP サーバーが起動する
- [ ] Claude Code から認識される
- [ ] Permission Prompt を受信できる
- [ ] 承認/拒否のレスポンスが機能する
- [ ] リモートからの操作が可能
- [ ] タイムアウト処理が適切

#### 4.2 課題の洗い出し
- 技術的な問題点
- 実装の難易度
- 運用上の課題

## 必要なリソース

### 開発環境
- Python 3.13+
- Flask/FastAPI (HTTP実装用)
- ngrok (外部公開テスト用)

### 参考資料
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Code SDK Docs](https://docs.anthropic.com/en/docs/claude-code/sdk)
- 既存の MCP 実装例（もしあれば）

## 検証スケジュール案

**Day 1 (3-4時間)**
- Phase 1: 最小限の実装と基本動作確認
- Phase 2 の準備

**Day 2 (3-4時間)**
- Phase 2: HTTP/WebSocket 実装
- Phase 3: 実用性検証

**Day 3 (1時間)**
- Phase 4: 結果まとめと判定

## リスクと対策

### リスク1: ドキュメント不足
**対策:** 
- MCP の仕様書を直接参照
- 試行錯誤でプロトコルを解析
- コミュニティに質問投稿

### リスク2: Claude Code の内部実装に依存
**対策:**
- 複数のアプローチを試す
- デバッグログを詳細に記録
- 公式サポートへの問い合わせ準備

### リスク3: セキュリティの考慮不足
**対策:**
- 検証環境は隔離する
- 認証機能は後回しにする
- 本番利用は別途設計

## 判定基準

### 実現可能と判断する条件
1. Phase 2 まで完了し、基本的な承認フローが動作
2. レスポンス時間が5秒以内
3. 安定して動作する

### 実現困難と判断する条件
1. Phase 1 で MCP サーバーが認識されない
2. Permission Prompt の仕様が不明確で進められない
3. 致命的な制限事項が発見される

## 代替案

検証が失敗した場合の代替アプローチ：

1. **セミオート承認**
   - 危険なコマンドのみ手動確認
   - 安全なコマンドは自動承認

2. **事前承認リスト**
   - よく使うコマンドを事前登録
   - パターンマッチで自動承認

3. **Claude Code の改善待ち**
   - 公式の実装例を待つ
   - コミュニティの進展を注視

## まとめ

この検証計画により、最小限の工数（合計7-9時間）でリモート承認機能の実現性を判断できます。Phase 1 の結果次第で早期に判断することも可能です。

## 実装進捗

### Phase 1 実装状況 (2025-07-22)

#### 完了した作業
1. **作業ブランチの作成**
   - `yuya-takeyama/feat/remote-approval-mcp` ブランチを作成

2. **MCPサーバーディレクトリ構築**
   - `mcp-server/` ディレクトリを作成
   - 専用の実装環境を整備

3. **最小限のMCPサーバー実装**
   - `minimal_mcp_server.py` を実装
   - JSON-RPC 2.0 ベースの通信実装
   - 初期化ハンドシェイク処理
   - 全ての権限リクエストを自動承認する機能
   - デバッグログ機能

4. **設定ファイルの作成**
   - `claude_settings_example.json` - Claude Code用の設定サンプル
   - uv経由での実行設定（相対パス使用）
   - cwdパラメータでプロジェクトルートを指定

5. **ドキュメント作成**
   - `mcp-server/README.md` - セットアップ手順と使用方法

#### 技術的な発見
- MCP は JSON-RPC 2.0 プロトコルを使用
- stdio transport で標準入出力を介した通信が可能
- Claude Code の mcpServers 設定で外部サーバーを登録可能

#### 次のステップ
1. Claude Code に設定を追加して実際の動作確認
2. Permission Prompt が実際に発行されるか検証
3. ログファイルでの通信内容の分析

### Phase 1 検証結果 (2025-07-22)

#### 発見事項

1. **MCP設定方法の違い**
   - 当初は `settings.json` への直接記載を試みたが、正式には `claude mcp add` コマンドを使用する必要がある
   - プロジェクトローカルの `.claude/settings.json` にも記載可能だが、動作検証が必要

2. **実装上の課題**
   - MCPサーバーが起動していることを確認できない（プロセスが見つからない）
   - ログファイルが生成されていない（サーバーが呼び出されていない可能性）
   - Permission Prompt がどのタイミングで発行されるか不明確

3. **技術的な理解**
   - stdio transport を使用した JSON-RPC 2.0 通信の基本実装は完了
   - 初期化ハンドシェイクと権限承認のレスポンス形式を実装

#### 問題点と改善案

1. **MCPサーバーの起動確認**
   - Claude Code が MCP サーバーをいつ、どのように起動するか不明
   - Permission Prompt が実際に使用されているか確認が必要

2. **デバッグの困難さ**
   - ログ出力が確認できないため、通信内容を把握できない
   - 標準エラー出力へのログ追加を検討

3. **ドキュメントの不足**
   - Custom Permission Prompt Tool の具体的な仕様が不明確
   - 実装例やテスト方法の情報が不足

#### Phase 1 判定結果

**部分的成功** - 基本的なMCPサーバーの実装は完了したが、Claude Codeとの統合が確認できていない。以下の追加検証が必要：

1. `claude mcp add` コマンドでの正式な登録と動作確認
2. Permission Prompt が実際に発行される条件の特定
3. 通信ログの取得方法の確立

### 追加検証 (2025-07-22)

#### MCPサーバー登録成功
- `claude mcp add` コマンドで正常に登録完了
- `claude mcp list` で登録確認済み

#### 未解決の課題
1. **MCPサーバーが起動しない**
   - プロセスが確認できない
   - ログファイルが生成されない
   - Permission Promptの発行条件が不明

2. **Permission Promptのトリガー**
   - どのような操作でPermission Promptが発行されるか不明
   - Claude Codeのドキュメントに具体的な記載なし
   - MCPサーバーとの通信が発生していない可能性

3. **デバッグの困難さ**
   - MCPサーバーの起動タイミングが不明
   - エラー情報が取得できない
   - 標準エラー出力への追加ログ実装済み

#### 仮説
- Permission Promptは現在のClaude Codeバージョンでは実装されていない可能性
- または特定の条件（設定、ツール使用パターン）でのみ発行される
- MCPサーバーは常時起動ではなくオンデマンド起動の可能性

## Phase 2: 公式SDK を使用した再実装計画

### 発見事項
1. **公式 Python SDK の存在**
   - GitHub: `https://github.com/modelcontextprotocol/python-sdk`
   - 完全なMCP仕様の実装
   - stdio、SSE、HTTP transportのサポート

2. **Claude Code のサポート状況**
   - stdio、SSE、HTTP の3つのtransportをサポート
   - OAuth 2.0認証のサポート
   - 環境変数の展開機能

3. **FastMCP API の発見** (2025-07-22)
   - `mcp.server.FastMCP` - デコレーターベースの高レベルAPI
   - ツール、リソース、プロンプトの簡単な登録
   - Context オブジェクトによるログ出力と進捗報告
   - 3つのトランスポート: stdio, sse, streamable-http

### 実装計画

#### 準備作業（1時間）
1. 公式SDKのインストールと依存関係の設定
2. SDKのドキュメントとサンプルコードの調査
3. Permission Prompt Toolの仕様確認

#### 基本実装（2-3時間）
1. **SDK ベースのMCPサーバー実装**
   - `mcp.server` を使用した標準的な実装
   - stdio transport の設定
   - 適切なエラーハンドリング

2. **Permission Handler の実装**
   - Permission prompt のリクエストを処理
   - 承認/拒否のレスポンス生成
   - タイムアウト処理

3. **デバッグ機能の実装**
   - 詳細なログ出力
   - リクエスト/レスポンスの記録
   - エラー情報の収集

#### 統合テスト（1時間）
1. Claude Code への登録と起動確認
2. Permission Prompt の発行条件の特定
3. 通信プロトコルの動作確認

#### リモート承認の実装（2-3時間）
1. **HTTP/WebSocket サーバーの追加**
   - SDKのHTTP transportを使用
   - リモートアクセス用のエンドポイント

2. **Web インターフェース**
   - 承認待ちリクエストの表示
   - 承認/拒否ボタン
   - リアルタイム更新

3. **セキュリティ対策**
   - 認証トークンの実装
   - HTTPS の設定
   - アクセス制限

### 技術スタック
- **言語**: Python 3.11+
- **MCP SDK**: modelcontextprotocol/python-sdk
- **Web Framework**: FastAPI または Flask
- **WebSocket**: websockets ライブラリ
- **Frontend**: 簡易HTML + JavaScript

### 成功基準
1. SDK を使用したMCPサーバーが正常に起動する
2. Claude Code から認識され、通信が確立する
3. Permission Prompt を受信して処理できる
4. リモートからの承認/拒否が機能する

### リスクと対策
1. **SDK の学習曲線**
   - 公式ドキュメントとサンプルコードを活用
   - 段階的な実装アプローチ

2. **Permission Prompt の仕様不明**
   - 実験的アプローチで仕様を推測
   - コミュニティやフォーラムでの情報収集

3. **ネットワークセキュリティ**
   - ローカルネットワーク内での初期テスト
   - 段階的なセキュリティ強化

### Phase 2 実装進捗 (2025-07-22)

#### 完了した作業
1. **MCPの依存関係追加**
   - cchh本体の pyproject.toml に MCP SDK を追加
   - mcp-server 専用の環境構築は不要と判断（cchh と統合）
   - `uv sync` で正常にインストール完了

2. **SDK調査完了**
   - FastMCP API の存在を確認
   - デコレーターベースの簡潔な実装方法を発見
   - サンプルコードと実装パターンを理解

#### 技術的な発見
- FastMCP は Flask/FastAPI ライクな API 設計
- Context オブジェクトでログ出力、進捗報告、リソース読み込みが可能
- stdio/sse/streamable-http の3つのトランスポートをサポート

#### 次のステップ
1. FastMCP を使用した MCP サーバーの実装
2. Permission Prompt の処理実装（具体的な仕様は実験的に確認）
3. デバッグログ機能の組み込み

### Phase 2 実装完了 (2025-07-22)

#### 実装内容
1. **FastMCP によるMCPサーバー実装**
   - `mcp_server_sdk.py` - FastMCP を使用した承認サーバー
   - 3つのツール実装：request_approval, list_pending_approvals, approve_request
   - Context によるログ出力と進捗報告機能
   - デバッグログ機能（`~/.cchh/mcp_logs/` に出力）

2. **テストツールの作成**
   - `test_mcp_sdk.py` - JSON-RPC プロトコルでの通信テスト
   - 初期化、ツールリスト、ツール呼び出しの動作確認

3. **Claude Code への統合**
   - ラッパースクリプト `run_mcp_server.sh` の作成
   - `claude mcp add` コマンドでの登録完了
   - 登録名: `cchh-remote-approval`

#### 技術的な確認事項
- MCPサーバーが正常に起動し、JSON-RPC通信が可能
- FastMCP のツール定義が正しく動作
- 承認リクエストの作成と自動承認が機能

#### 次のステップ
1. Claude Code を再起動して MCP サーバーの認識確認
2. Permission Prompt の実際の発行条件を確認
3. リモート承認機能の実装（HTTP/WebSocket）

### Permission Prompt Tool 実装完了 (2025-07-22)

#### 実装内容
1. **approval_prompt ツールの追加**
   - Claude Code SDK ドキュメントに準拠した実装
   - tool_name, input, tool_use_id を受け取る
   - JSON文字列化された allow/deny レスポンスを返す
   - デモ用ロジック：inputに "allow" が含まれていれば承認

2. **発見事項**
   - --permission-prompt-tool オプションは --help に表示されない
   - SDK ドキュメントにのみ記載されている可能性
   - MCPサーバーは4つのツールを持つ状態に

#### 未解決の課題
- --permission-prompt-tool オプションの指定方法が不明
- Claude Code が自動的に approval_prompt を認識するかは未確認
- 実際の Permission Prompt 発行条件が不明

### Permission Prompt Tool 動作確認完了！(2025-07-22)

#### 動作確認結果
1. **approval_prompt が正常に動作**
   - 許可されていないコマンド（rm, tail）で "Permission denied by cchh-remote-approval" 
   - Read ツールも同様に拒否される
   - ファイル名に "allow" を含む場合は承認される

2. **確認できた挙動**
   - --permission-prompt-tool オプションで MCP サーバーが認識される
   - 許可リストにないツール/コマンドで approval_prompt が呼ばれる
   - approval_prompt の返り値によって承認/拒否が決定

3. **技術的発見**
   - Permission Prompt は通常のMCPツールとして実装可能
   - input パラメータにツールの引数が含まれる
   - JSON文字列で allow/deny レスポンスを返す仕組み

#### 次のステップ
- HTTP/WebSocket でリモート承認を実装
- Slack や Web UI から承認/拒否できる仕組みの構築