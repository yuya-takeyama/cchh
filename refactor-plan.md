# Python Scripts Refactoring Plan 📋

## 方針：単一エントリーポイント + 内部モジュール化 🎯

開発初期段階では、設定ファイルを頻繁に変更せずに済む**単一エントリーポイント方式**を採用します。

### 利点
- 設定ファイル（settings.json）の変更が不要
- 要件変更に柔軟に対応可能
- 全イベントを一箇所で処理できるため、デバッグが容易
- uv run での実行が統一的

## 現状分析 🔍

現在の`hook_handler.py`は、全てのClaude Codeイベントを受け取り、内部で処理を分岐しています：

1. **セッション管理** - 新規セッション時のcwd表示
2. **Slack通知** - 各種イベントをSlackに通知
3. **ずんだもん音声通知** - プロンプト送信時の音声読み上げ
4. **イベントロギング** - 全イベントをJSONLファイルに記録
5. **コマンド美化** - Bashコマンドを日本語に変換

その他の独立したスクリプト：
- **Ruff Format Hook** (`ruff_format_hook.py`) - ファイル編集後の自動フォーマット

## リファクタリング方針 🚀

### 1. ディレクトリ構造

```
cchh/
├── pyproject.toml                      # プロジェクト設定
├── uv.lock
├── README.md
├── DEVELOPER.md
├── LICENSE
├── aqua/
│
# メインエントリーポイント
├── hook_handler.py                     # 全イベントを処理するメインスクリプト
├── ruff_format_hook.py                 # Ruffフォーマット専用（既存のまま）
│
├── src/                                # 内部モジュール
│   ├── __init__.py
│   ├── core/                           # コア機能
│   │   ├── __init__.py
│   │   ├── dispatcher.py               # イベントディスパッチャー
│   │   ├── session.py                  # セッション管理
│   │   └── types.py                    # 型定義（HookEvent等）
│   │
│   ├── handlers/                       # イベントハンドラー
│   │   ├── __init__.py
│   │   ├── base.py                    # ベースハンドラークラス
│   │   ├── pre_tool_use.py            # PreToolUseハンドラー
│   │   ├── post_tool_use.py           # PostToolUseハンドラー
│   │   ├── user_prompt_submit.py      # UserPromptSubmitハンドラー
│   │   ├── notification.py            # Notificationハンドラー
│   │   ├── stop.py                    # Stop/SubagentStopハンドラー
│   │   └── pre_compact.py             # PreCompactハンドラー
│   │
│   ├── features/                       # 機能実装
│   │   ├── __init__.py
│   │   ├── session_notifier.py        # セッション開始通知
│   │   ├── slack_notifier.py          # Slack通知
│   │   ├── zunda_speaker.py           # ずんだもん音声
│   │   ├── event_logger.py            # イベントロギング
│   │   └── command_beautifier.py      # コマンド美化
│   │
│   └── utils/                          # ユーティリティ
│       ├── __init__.py
│       ├── config.py                   # 設定管理
│       ├── logger.py                   # ロギング基盤
│       └── io_helpers.py              # JSON I/O等
│
└── tests/                              # テストディレクトリ
    ├── __init__.py
    ├── conftest.py
    ├── test_hook_handler.py            # メインハンドラーのテスト
    ├── core/
    │   ├── test_dispatcher.py
    │   └── test_session.py
    ├── handlers/
    │   ├── test_pre_tool_use.py
    │   └── ...
    ├── features/
    │   ├── test_slack_notifier.py
    │   ├── test_zunda_speaker.py
    │   └── ...
    └── integration/
        └── test_real_events.py
```

### 2. 実装アーキテクチャ 🏗️

#### hook_handler.py の構造

```python
#!/usr/bin/env python3
"""Claude Code Hook Handler - 全イベントを処理"""

import json
import sys
from src.core.dispatcher import EventDispatcher
from src.utils.io_helpers import load_hook_event

def main():
    # イベントデータを読み込み
    event = load_hook_event(sys.stdin)
    
    # ディスパッチャーで適切なハンドラーに振り分け
    dispatcher = EventDispatcher()
    dispatcher.dispatch(event)
    
    # 元のイベントデータを出力（透過性を保つ）
    print(json.dumps(event.to_dict()))

if __name__ == "__main__":
    main()
```

#### イベントディスパッチャー

```python
# src/core/dispatcher.py
class EventDispatcher:
    def __init__(self):
        self.handlers = self._init_handlers()
        self.features = self._init_features()
    
    def dispatch(self, event: HookEvent):
        # イベントタイプに応じてハンドラーを実行
        handler = self.handlers.get(event.hook_event_name)
        if handler:
            handler.handle(event, self.features)
```

#### 機能の分離

各機能は独立したクラスとして実装し、必要に応じて有効/無効を切り替え可能：

```python
# src/features/slack_notifier.py
class SlackNotifier:
    def __init__(self):
        self.enabled = os.getenv("SLACK_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    
    def notify(self, event: HookEvent, message: str):
        if not self.enabled:
            return
        # Slack通知の実装
```

### 3. Claude Code設定（settings.json）

現状の設定をそのまま維持：

```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "cd ~/cchh && uv run python hook_handler.py"
      }]
    }],
    "PostToolUse": [{
      "hooks": [
        {
          "type": "command",
          "command": "cd ~/cchh && uv run python hook_handler.py"
        },
        {
          "type": "command",
          "command": "cd ~/cchh && uv run python ruff_format_hook.py"
        }
      ]
    }],
    // ... 他のイベントも同様
  }
}
```

### 4. 機能の有効/無効制御 🎛️

環境変数や設定ファイルで機能を制御：

```bash
# .env または環境変数
SLACK_NOTIFICATIONS_ENABLED=true
ZUNDA_SPEAKER_ENABLED=true
EVENT_LOGGING_ENABLED=true
SESSION_NOTIFIER_ENABLED=true
COMMAND_BEAUTIFIER_ENABLED=true

# 特定のイベントでのみ有効化
SLACK_NOTIFY_ON_TOOL_USE=true
SLACK_NOTIFY_ON_STOP=true
ZUNDA_SPEAK_ON_PROMPT_SUBMIT=true
```

### 5. 移行手順 📝

1. **ディレクトリ構造の作成**
   - `src/` とサブディレクトリを作成
   - テストディレクトリを整理

2. **既存コードのモジュール化**
   - `hook_handler/` の機能を `src/` 配下に分割
   - 各機能を独立したクラスとして実装

3. **メインハンドラーの更新**
   - `hook_handler.py` をディスパッチャーパターンに変更
   - 全イベントを受け取って適切に振り分け

4. **テストの更新**
   - モジュール化に合わせてテストを更新
   - 統合テストを追加

5. **ドキュメントの更新**
   - README.mdに新しい構造を反映
   - 環境変数の説明を追加

### 6. 将来の拡張性 🔮

要件が安定してきたら、以下の移行が可能：

1. **個別フック化**
   - 各機能を独立したスクリプトに分離
   - settings.jsonで個別に登録

2. **CLIツール化**
   - サブコマンド形式のCLIツールに統合
   - `cchh hook`, `cchh format` などのコマンド体系

3. **プラグインシステム**
   - 新機能を簡単に追加できるプラグイン機構
   - 外部パッケージからの機能追加

## まとめ ✨

このリファクタリングにより：
- **設定変更なし**で機能の追加・変更が可能
- **内部モジュール化**により保守性向上
- **単一エントリーポイント**でデバッグが容易
- **uv run** での統一的な実行
- 将来的な拡張への道筋も確保

開発初期の柔軟性を保ちながら、コードの品質を向上させる実践的なアプローチです！