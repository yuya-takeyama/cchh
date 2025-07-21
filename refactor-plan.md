# Python Scripts Refactoring Plan 📋

## Claude Code Hooks の正しい理解 🎯

Claude Code Hooksは、Claude Codeの特定のイベントに対してカスタムコマンドを実行する仕組みです。
各フックは**完全に独立**しており、設定ファイルで個別に登録されます。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {"type": "command", "command": "/path/to/slack_notifier.py"},
          {"type": "command", "command": "/path/to/ruff_format.py"}
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {"type": "command", "command": "/path/to/zunda_speaker.py"}
        ]
      }
    ]
  }
}
```

## 現状分析 🔍

現在の`hook_handler.py`は、本来独立すべき複数の機能を1つにまとめてしまっています：

1. **セッション開始通知** - 新規セッション時のcwd表示
2. **Slack通知** - 各種イベントをSlackに通知
3. **ずんだもん音声通知** - プロンプト送信時の音声読み上げ
4. **イベントロギング** - 全イベントをJSONLファイルに記録
5. **コマンド美化** - Bashコマンドを日本語に変換

その他の独立したスクリプト：
- **Ruff Format Hook** (`ruff_format_hook.py`) - ファイル編集後の自動フォーマット
- **Event Logger** (`event_logger.sh`) - シェルスクリプト版のイベントロガー

## リファクタリング方針 🎯

### 1. ディレクトリ構造

```
cchh/
├── pyproject.toml                      # プロジェクト設定（統一）
├── uv.lock
├── README.md
├── DEVELOPER.md
├── LICENSE
├── aqua/
│
# 独立したフックスクリプト（Claude Code設定で個別に登録）
├── session_notifier.py                 # セッション開始時のcwd表示等
├── slack_notifier.py                   # Slack通知フック
├── zunda_speaker.py                    # ずんだもん音声通知フック
├── event_logger.py                     # イベントロギングフック
├── command_beautifier.py               # コマンド美化フック（Slack連携用）
├── ruff_format.py                      # Ruffフォーマットフック
│
├── src/                                # 共通パッケージディレクトリ
│   ├── __init__.py
│   ├── shared/                         # 共通ユーティリティ
│   │   ├── __init__.py
│   │   ├── types.py                    # HookEvent等の型定義
│   │   ├── utils.py                    # JSON I/O、セッション管理等
│   │   ├── constants.py                # 共通定数
│   │   └── session.py                  # セッション管理ロジック
│   │
│   ├── notifiers/                      # 通知実装
│   │   ├── __init__.py
│   │   ├── slack.py                    # Slack通知実装
│   │   └── zunda.py                    # ずんだもん音声実装
│   │
│   ├── formatters/                     # フォーマッター実装
│   │   ├── __init__.py
│   │   ├── command.py                  # コマンド変換ロジック
│   │   └── ruff.py                     # Ruffフォーマットロジック
│   │
│   └── loggers/                        # ロガー実装
│       ├── __init__.py
│       └── event.py                    # イベントロギング実装
│
└── tests/                              # テストディレクトリ
    ├── __init__.py
    ├── conftest.py                     # pytest共通設定
    ├── test_session_notifier.py
    ├── test_slack_notifier.py
    ├── test_zunda_speaker.py
    ├── test_event_logger.py
    ├── test_command_beautifier.py
    ├── test_ruff_format.py
    └── integration/                    # 統合テスト
        ├── test_hook_combinations.py   # 複数フックの組み合わせテスト
        └── test_real_events.py         # 実際のイベントデータでのテスト
```

### 2. 各フックスクリプトの役割 📝

#### session_notifier.py
- **イベント**: PreToolUse（最初のツール使用時）
- **機能**: 新規セッション開始時にcwdを表示
- **設定例**: 
  ```json
  "PreToolUse": [{
    "hooks": [{"type": "command", "command": "./session_notifier.py"}]
  }]
  ```

#### slack_notifier.py
- **イベント**: PostToolUse, Notification, Stop等
- **機能**: 各種イベントをSlackに通知
- **設定例**:
  ```json
  "PostToolUse": [{
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [{"type": "command", "command": "./slack_notifier.py"}]
  }]
  ```

#### zunda_speaker.py
- **イベント**: UserPromptSubmit
- **機能**: ユーザープロンプトをずんだもんが読み上げ
- **設定例**:
  ```json
  "UserPromptSubmit": [{
    "hooks": [{"type": "command", "command": "./zunda_speaker.py"}]
  }]
  ```

#### event_logger.py
- **イベント**: 全イベント
- **機能**: イベントデータをJSONLファイルに記録
- **設定例**: 各イベントに追加

#### command_beautifier.py
- **イベント**: PreToolUse（Bashツール使用時）
- **機能**: Bashコマンドを日本語に変換してSlackに送信
- **設定例**:
  ```json
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "./command_beautifier.py"}]
  }]
  ```

#### ruff_format.py
- **イベント**: PostToolUse（ファイル編集後）
- **機能**: Pythonファイルを自動フォーマット
- **設定例**:
  ```json
  "PostToolUse": [{
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [{"type": "command", "command": "./ruff_format.py"}]
  }]
  ```

### 3. 実装の詳細 📝

#### 3.1 各フックスクリプトの実装パターン

各フックは以下の基本構造を持ちます：

```python
#!/usr/bin/env python3
"""セッション開始通知フック"""

import json
import sys
from src.shared.utils import load_hook_event
from src.shared.session import SessionManager

def main():
    # イベントデータを読み込み
    event = load_hook_event(sys.stdin)
    
    # セッション管理
    session_mgr = SessionManager(event.session_id)
    
    # 新規セッションの場合のみ処理
    if session_mgr.is_new_session:
        # cwd表示などの処理
        print(f"📁 Working directory: {event.cwd}")
    
    # 正常終了
    sys.exit(0)

if __name__ == "__main__":
    main()
```

#### 3.2 共通機能の抽出

以下の機能を `src.shared` に抽出：
- `HookEvent` - イベントデータの型定義
- `load_hook_event()` - JSON入力のパース
- `SessionManager` - セッション状態の管理
- 各種設定の読み込み（環境変数、設定ファイル）

#### 3.3 フック間の連携

各フックは**完全に独立**していますが、必要に応じて連携できます：

1. **直接連携なし** - Claude Codeが各フックを個別に呼び出す
2. **データ共有** - 必要に応じてファイルやDBを介して状態を共有
3. **設定の統一** - 環境変数や設定ファイルで挙動を制御

### 4. テスト・リント・フォーマット・型チェックの統合 🧪

`pyproject.toml` の taskipy 設定を更新：

```toml
[tool.taskipy.tasks]
test = "pytest tests/"
lint = "ruff check ."
format = "ruff format ."
typecheck = "mypy src/ *.py"
all = "task format && task lint && task typecheck && task test"
```

### 5. 移行手順 🚀

1. **作業ブランチの作成**
   - `yuya-takeyama/feat/refactor-python-scripts`

2. **ディレクトリ構造の作成**
   - `src/` とサブパッケージの作成
   - `tests/` の再構成

3. **コードの分割と移行**
   - 既存の `hook_handler/` から機能を分割：
     - セッション管理 → `session_notifier.py`
     - Slack通知 → `slack_notifier.py`
     - ずんだもん通知 → `zunda_speaker.py`
     - イベントロギング → `event_logger.py`
     - コマンド美化 → `command_beautifier.py`
   - `ruff_format_hook.py` → `ruff_format.py` にリネーム
   - 共通ロジックを `src/` に抽出

4. **各フックスクリプトの作成**
   - 各機能を独立したスクリプトとして実装
   - 共通処理は `src/` のモジュールを利用

5. **テストの移行と更新**
   - 既存のテストを新しい構造に合わせて移行
   - import パスの更新

6. **設定ファイルの更新**
   - `pyproject.toml` の更新
   - GitHub Actions や他の CI/CD 設定の更新（必要に応じて）

### 6. Claude Code設定の例 ⚙️

リファクタリング後のClaude Code設定（`.claude/settings.json`）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {"type": "command", "command": "~/cchh/session_notifier.py"},
          {"type": "command", "command": "~/cchh/event_logger.py"}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "~/cchh/command_beautifier.py"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {"type": "command", "command": "~/cchh/slack_notifier.py"},
          {"type": "command", "command": "~/cchh/ruff_format.py"},
          {"type": "command", "command": "~/cchh/event_logger.py"}
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {"type": "command", "command": "~/cchh/zunda_speaker.py"},
          {"type": "command", "command": "~/cchh/event_logger.py"}
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {"type": "command", "command": "~/cchh/slack_notifier.py"},
          {"type": "command", "command": "~/cchh/event_logger.py"}
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {"type": "command", "command": "~/cchh/slack_notifier.py"},
          {"type": "command", "command": "~/cchh/event_logger.py"}
        ]
      }
    ]
  }
}
```

### 7. 移行のメリット 🎯

1. **明確な責任分離**
   - 各フックが単一の責任を持つ
   - デバッグとテストが容易

2. **柔軟な組み合わせ**
   - 必要なフックだけを有効化
   - イベントごとに異なる組み合わせが可能

3. **保守性の向上**
   - 機能追加が簡単（新しいフックスクリプトを追加するだけ）
   - 既存機能への影響が最小限

4. **パフォーマンス**
   - 必要な処理だけを実行
   - 並列実行による高速化

## まとめ ✨

このリファクタリングにより：
- Claude Code Hooksの仕組みに沿った正しい設計
- 各機能が独立したスクリプトとして動作
- 設定ファイルで柔軟に組み合わせ可能
- デバッグ・テスト・保守が容易
- 新機能の追加が簡単

次のセッションでこの計画に基づいて実装を進めていきます！