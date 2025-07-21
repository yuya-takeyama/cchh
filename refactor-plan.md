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

1. **Slack通知機能**
   - セッション開始時のcwd表示
   - 各種イベントをSlackに通知
   - 長すぎるコマンドは適宜省略（省略箇所は明示）

2. **ずんだもん音声通知機能**
   - プロンプト送信時の音声読み上げ
   - Bashコマンドを音声用に簡略化

3. **イベントロギング機能**
   - 全イベントをJSONLファイルに記録

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
├── all_hooks.py                        # 全イベントを処理するメインスクリプト
├── ruff_hook.py                        # Ruffフォーマット専用
│
├── src/                                # 内部モジュール
│   ├── __init__.py
│   ├── core/                           # コア機能
│   │   ├── __init__.py
│   │   ├── dispatcher.py               # イベントディスパッチャー
│   │   ├── session.py                  # セッション管理
│   │   └── types.py                    # 型定義（HookEvent等）
│   │
│   ├── slack/                          # Slack通知機能（完全独立）
│   │   ├── __init__.py
│   │   ├── notifier.py                 # Slack通知のメイン実装
│   │   ├── session_handler.py         # セッション開始時のcwd表示（Slack用）
│   │   ├── event_formatter.py         # イベントメッセージのフォーマット
│   │   ├── command_formatter.py       # Bashコマンドの整形（詳細版）
│   │   └── config.py                   # Slack固有の設定
│   │
│   ├── zunda/                          # ずんだもん音声機能（完全独立）
│   │   ├── __init__.py
│   │   ├── speaker.py                  # 音声読み上げのメイン実装
│   │   ├── prompt_formatter.py        # プロンプトの音声用整形
│   │   ├── command_formatter.py       # Bashコマンドの整形（簡略版）
│   │   └── config.py                   # ずんだもん固有の設定
│   │
│   ├── logger/                         # イベントロギング機能
│   │   ├── __init__.py
│   │   ├── event_logger.py             # JSONLファイルへのロギング
│   │   └── config.py                   # ロガー設定
│   │
│   └── utils/                          # 共通ユーティリティ
│       ├── __init__.py
│       ├── command_parser.py           # Bashコマンドのパース（共通処理）
│       ├── text_utils.py               # テキスト処理（長文省略等）
│       ├── config.py                   # 全体共通設定
│       ├── logger.py                   # デバッグ用ロガー
│       └── io_helpers.py              # JSON I/O等
│
└── tests/                              # テストディレクトリ
    ├── __init__.py
    ├── conftest.py
    ├── test_all_hooks.py               # メインハンドラーのテスト
    ├── core/
    │   ├── test_dispatcher.py
    │   └── test_session.py
    ├── slack/
    │   ├── test_notifier.py
    │   ├── test_session_handler.py
    │   └── test_command_formatter.py
    ├── zunda/
    │   ├── test_speaker.py
    │   ├── test_prompt_formatter.py
    │   └── test_command_formatter.py
    ├── logger/
    │   └── test_event_logger.py
    └── integration/
        └── test_real_events.py
```

### 2. 実装アーキテクチャ 🏗️

#### all_hooks.py の構造

```python
#!/usr/bin/env python3
"""Claude Code All Hooks Handler - 全イベントを処理"""

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
        # 各機能を初期化（完全に独立）
        self.slack = self._init_slack()
        self.zunda = self._init_zunda()
        self.logger = self._init_logger()
    
    def dispatch(self, event: HookEvent):
        # 各機能に並列でイベントを渡す（それぞれが独立して判断）
        if self.slack:
            self.slack.handle_event(event)
        if self.zunda:
            self.zunda.handle_event(event)
        if self.logger:
            self.logger.handle_event(event)
```

#### 機能の完全分離

各機能は完全に独立したモジュールとして実装：

```python
# src/slack/notifier.py
class SlackNotifier:
    def __init__(self):
        self.enabled = os.getenv("SLACK_NOTIFICATIONS_ENABLED", "true").lower() == "true"
        self.session_handler = SessionHandler()  # Slack専用のセッション処理
        self.command_formatter = CommandFormatter()  # Slack専用のコマンド整形
    
    def handle_event(self, event: HookEvent):
        if not self.enabled:
            return
        
        # イベントタイプに応じて処理を分岐
        if event.hook_event_name == "PreToolUse":
            self._handle_pre_tool_use(event)
        elif event.hook_event_name == "UserPromptSubmit":
            self._handle_user_prompt(event)
        # ... 他のイベント
```

```python
# src/zunda/speaker.py
class ZundaSpeaker:
    def __init__(self):
        self.enabled = os.getenv("ZUNDA_SPEAKER_ENABLED", "true").lower() == "true"
        self.prompt_formatter = PromptFormatter()  # ずんだもん専用の整形
        self.command_formatter = CommandFormatter()  # ずんだもん専用の簡略化
    
    def handle_event(self, event: HookEvent):
        if not self.enabled:
            return
        
        # UserPromptSubmitイベントのみ処理
        if event.hook_event_name == "UserPromptSubmit":
            self._speak_prompt(event)
```

#### コマンド処理の共通化と特殊化

```python
# src/utils/command_parser.py（共通処理）
def parse_bash_command(command: str) -> dict:
    """Bashコマンドを解析して構造化"""
    # コマンド名、引数、オプションなどを抽出
    return {
        "command": "python3",
        "args": ["path/to/script.py"],
        "options": {"--verbose": True},
        "raw": command
    }

# src/slack/command_formatter.py（Slack用）
class CommandFormatter:
    def format(self, parsed_cmd: dict) -> str:
        """Slack通知用：長すぎる部分は省略して<snip>で明示"""
        raw = parsed_cmd["raw"]
        if len(raw) > 200:
            # 長すぎる引数は省略
            base = f"{parsed_cmd['command']} {parsed_cmd['args'][0]}"
            if len(parsed_cmd['args']) > 1:
                return f"{base} <snip>"
            return base
        return raw

# src/zunda/command_formatter.py（ずんだもん用）  
class CommandFormatter:
    def format(self, parsed_cmd: dict) -> str:
        """音声読み上げ用：超シンプルに"""
        cmd_map = {
            "python3": "パイソンを実行",
            "npm": "エヌピーエムを実行",
            "git": "ギットコマンド"
        }
        return cmd_map.get(parsed_cmd["command"], parsed_cmd["command"])
```

### 3. Claude Code設定（settings.json）

スクリプト名の変更のみ（構造は維持）：

```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "cd ~/cchh && uv run python all_hooks.py"
      }]
    }],
    "PostToolUse": [{
      "hooks": [
        {
          "type": "command",
          "command": "cd ~/cchh && uv run python all_hooks.py"
        },
        {
          "type": "command",
          "command": "cd ~/cchh && uv run python ruff_hook.py"
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
SLACK_NOTIFICATIONS_ENABLED=true        # Slack通知全体のON/OFF
ZUNDA_SPEAKER_ENABLED=true             # ずんだもん音声全体のON/OFF
EVENT_LOGGING_ENABLED=true             # イベントロギングのON/OFF

# Slack通知の詳細設定
SLACK_SHOW_SESSION_START=true          # セッション開始時のcwd表示
SLACK_NOTIFY_ON_TOOL_USE=true          # ツール使用時の通知
SLACK_NOTIFY_ON_STOP=true              # 処理終了時の通知
SLACK_COMMAND_MAX_LENGTH=200           # コマンド表示の最大文字数

# ずんだもん音声の詳細設定
ZUNDA_SPEAK_ON_PROMPT_SUBMIT=true      # プロンプト送信時の読み上げ
ZUNDA_SPEAK_SPEED=1.2                  # 読み上げ速度
```

### 5. 移行手順 📝

1. **ディレクトリ構造の作成**
   - `src/` とサブディレクトリを作成
   - テストディレクトリを整理

2. **既存コードのモジュール化**
   - `hook_handler/` の機能を `src/` 配下に分割
   - 各機能を独立したクラスとして実装

3. **メインハンドラーの更新**
   - `hook_handler.py` → `all_hooks.py` にリネーム
   - `ruff_format_hook.py` → `ruff_hook.py` にリネーム
   - ディスパッチャーパターンで実装
   - 全イベントを受け取って適切に振り分け

4. **テストの更新**
   - モジュール化に合わせてテストを更新
   - 統合テストを追加

5. **設定ファイルの更新**
   - settings.jsonのコマンドをall_hooks.py、ruff_hook.pyに変更

6. **ドキュメントの更新**
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
- **機能の完全分離** - Slack通知とずんだもん音声が独立して動作
- **設定変更なし**で機能の追加・変更が可能
- **内部モジュール化**により保守性向上
- **単一エントリーポイント**でデバッグが容易
- **uv run** での統一的な実行
- 各機能が独自のフォーマット処理を持つことで、用途に最適化
- 将来的な拡張への道筋も確保

開発初期の柔軟性を保ちながら、コードの品質を向上させる実践的なアプローチです！