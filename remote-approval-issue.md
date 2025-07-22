# Claude Code リモート承認機能の調査レポート

## 概要

Claude Code でコマンド実行時の許可をリモートで承認し、追加プロンプトも送信できるようにする可能性について調査しました。

## 現在の課題

- Claude Code でコマンド実行時に許可を求められると、そこでブロックされる
- 離席中（トイレ、お風呂など）に作業が止まってしまう
- Slack 通知で状況は確認できるが、承認操作ができない
- Claude Code Actions は Hooks が使えないため、通知も来ない

## Custom Permission Prompt Tool について

### 概要

Custom Permission Prompt Tool は、Claude Code SDK が提供する機能で、ツール実行前に動的に許可・拒否を制御できる MCP (Model Context Protocol) ツールです。

### 主な特徴

1. **動的な許可制御**
   - ツール実行前に外部システムから許可・拒否を決定できる
   - JSON レスポンスで `allow` または `deny` を返す

2. **通信プロトコル**
   - MCP は以下の通信方法をサポート：
     - stdio (標準入出力)
     - SSE (Server-Sent Events)
     - HTTP/HTTPS
     - WebSocket

3. **レスポンス形式**
   ```json
   {
     "behavior": "allow",  // または "deny"
     "updatedInput": {...},  // オプション：入力を修正可能
     "message": "説明メッセージ"  // deny時の理由
   }
   ```

## リモート承認実現の可能性

### 技術的には可能

1. **リモート MCP サーバーの構築**
   - HTTP/WebSocket 経由でリモート承認システムを構築可能
   - OAuth 認証もサポートされている

2. **承認フローの実装**
   - Slack Bot 経由で承認ボタンを表示
   - モバイルアプリから承認操作
   - Web インターフェースでの承認

### 現在の問題点

1. **実装例の不足**
   - 公式ドキュメントに動作する実装例がない
   - コミュニティも実装例を求めている ([GitHub Issue #1175](https://github.com/anthropics/claude-code/issues/1175))

2. **ドキュメントの不完全性**
   - 具体的な実装方法が不明確
   - エラーハンドリングやデバッグ方法が記載されていない

3. **コミュニティの取り組み**
   - いくつかの実装試行があるが、動作確認されたものがない
   - Telegram Bot でのデモは存在するが、詳細不明

## リモートプロンプト送信について

### 現状の制限

- Custom Permission Prompt Tool は承認/拒否の制御のみ
- プロンプトの追加送信機能は直接サポートされていない

### 可能な回避策

1. **updatedInput フィールドの活用**
   - 承認時に入力を修正して追加情報を含める

2. **別システムとの連携**
   - MCP サーバー経由で別のコミュニケーションチャネルを確立
   - WebSocket を使った双方向通信の実装

## 結論

### 実現可能性：△（理論的には可能だが、現実的には困難）

**理由：**
- 技術的な基盤（MCP、リモート通信）は存在する
- しかし、実装例やドキュメントが不足している
- コミュニティでも成功例がまだない

### 推奨される次のステップ

1. **短期的対応**
   - 現在の CCHH の Slack 通知を拡張
   - 承認が必要な場面を検知して通知を強化

2. **中期的対応**
   - Anthropic の公式実装例を待つ
   - コミュニティの進展を注視

3. **長期的対応**
   - MCP サーバーの独自実装に挑戦
   - HTTP/WebSocket ベースの承認システム構築

## 参考リンク

- [Claude Code SDK Documentation](https://docs.anthropic.com/en/docs/claude-code/sdk)
- [Model Context Protocol](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [GitHub Issue #1175](https://github.com/anthropics/claude-code/issues/1175)
- [Remote MCP Guide](https://support.anthropic.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
