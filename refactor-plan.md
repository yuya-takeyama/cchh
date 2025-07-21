# Python Scripts Refactoring Plan 📋

## 現状分析 🔍

現在のプロジェクトには以下の機能が含まれています：

1. **Claude Code Hook Handler** (`hook_handler.py` + `hook_handler/`)
   - Claude Code のイベントフックを処理する包括的なシステム
   - セッション管理、通知、ロギング、コマンド変換などを含む

2. **Ruff Format Hook** (`ruff_format_hook.py`)
   - Python ファイル編集後の自動フォーマット機能

3. **Event Logger** (`event_logger.sh`)
   - シェルスクリプトでイベントをJSONL形式で記録

4. **テストスクリプト群**
   - `test_cwd_display.py` - cwd表示機能のテスト
   - `test_user_prompt_submit.py` - UserPromptSubmitイベントのテスト
   - `test_hook_handler.py` - pytestランナー

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
├── claude_hook.py                      # Claude Code Hook Handler エントリーポイント
├── ruff_hook.py                        # Ruff Format Hook エントリーポイント
├── event_logger.py                     # Event Logger エントリーポイント (Pythonに移植)
│
├── src/                                # 共通パッケージディレクトリ
│   ├── __init__.py
│   ├── claude_hook/                    # Claude Hook Handler パッケージ
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   ├── session.py
│   │   ├── notifiers.py
│   │   ├── logger.py
│   │   ├── config.py
│   │   ├── messages.py
│   │   ├── command_converter.py
│   │   └── utils.py
│   │
│   ├── ruff_hook/                      # Ruff Hook パッケージ
│   │   ├── __init__.py
│   │   └── formatter.py
│   │
│   ├── event_logger/                   # Event Logger パッケージ
│   │   ├── __init__.py
│   │   └── logger.py
│   │
│   └── shared/                         # 共通ユーティリティ
│       ├── __init__.py
│       ├── types.py                    # 共通型定義
│       ├── utils.py                    # 共通ユーティリティ関数
│       └── constants.py                # 共通定数
│
└── tests/                              # 統合テストディレクトリ
    ├── __init__.py
    ├── conftest.py                     # pytest共通設定
    ├── claude_hook/
    │   ├── test_handlers.py
    │   ├── test_session.py
    │   ├── test_notifiers.py
    │   ├── test_logger.py
    │   ├── test_command_converter.py
    │   └── test_utils.py
    ├── ruff_hook/
    │   └── test_formatter.py
    ├── event_logger/
    │   └── test_logger.py
    └── integration/                    # 統合テスト
        ├── test_cwd_display.py
        └── test_user_prompt_submit.py
```

### 2. 命名規則とパッケージ名の提案 💫

#### エントリーポイント（root ディレクトリ）
- `claude_hook.py` - Claude Code のフックハンドラー
- `ruff_hook.py` - Ruff フォーマッターフック  
- `event_logger.py` - イベントロガー（Pythonに移植）

#### パッケージ名（src/ 内）
- `src.claude_hook` - Claude フック関連機能
- `src.ruff_hook` - Ruff フォーマット関連機能
- `src.event_logger` - イベントロギング機能
- `src.shared` - 共通ユーティリティ

### 3. 実装の詳細 📝

#### 3.1 エントリーポイントの実装パターン

各エントリーポイントは以下のパターンに従います：

```python
#!/usr/bin/env python3
"""Claude Code hook handler entry point"""

from src.claude_hook import main

if __name__ == "__main__":
    main()
```

#### 3.2 共通機能の抽出

以下の機能を `src.shared` に抽出：
- HookEvent の型定義
- JSON入出力のヘルパー関数
- ロギング基盤クラス
- 設定管理の基底クラス

#### 3.3 event_logger.sh の Python 移植

現在のシェルスクリプトを Python に移植し、他のツールと統一された環境で実行：

```python
# event_logger.py
import json
import sys
from pathlib import Path
from src.event_logger import EventLogger

def main():
    logger = EventLogger()
    event_data = json.load(sys.stdin)
    logger.log_event(event_data)
```

### 4. テスト・リント・フォーマット・型チェックの統合 🧪

`pyproject.toml` の taskipy 設定を更新：

```toml
[tool.taskipy.tasks]
test = "pytest tests/"
test-claude = "pytest tests/claude_hook/"
test-ruff = "pytest tests/ruff_hook/"
test-logger = "pytest tests/event_logger/"
test-integration = "pytest tests/integration/"
lint = "ruff check ."
format = "ruff format ."
typecheck = "mypy src/ claude_hook.py ruff_hook.py event_logger.py"
all = "task format && task lint && task typecheck && task test"
```

### 5. 移行手順 🚀

1. **作業ブランチの作成**
   - `yuya-takeyama/feat/refactor-python-scripts`

2. **ディレクトリ構造の作成**
   - `src/` とサブパッケージの作成
   - `tests/` の再構成

3. **コードの移動と分割**
   - 既存の `hook_handler/` から機能を `src/claude_hook/` へ
   - `ruff_format_hook.py` を `src/ruff_hook/` へ
   - event_logger.sh を Python に移植して `src/event_logger/` へ

4. **エントリーポイントの作成**
   - `claude_hook.py`, `ruff_hook.py`, `event_logger.py` を root に配置

5. **テストの移行と更新**
   - 既存のテストを新しい構造に合わせて移行
   - import パスの更新

6. **設定ファイルの更新**
   - `pyproject.toml` の更新
   - GitHub Actions や他の CI/CD 設定の更新（必要に応じて）

### 6. Python コミュニティの標準との整合性 🐍

この構造は以下の Python 標準に準拠しています：

- **src レイアウト**: `src/` ディレクトリを使用することで、開発時のインポートエラーを防ぐ
- **パッケージ構造**: 機能ごとにパッケージを分割し、再利用性を高める
- **テスト構造**: `tests/` ディレクトリをパッケージ構造にミラーリング
- **エントリーポイント**: スクリプトとして実行可能なファイルを root に配置
- **命名規則**: PEP 8 に準拠（snake_case for modules/packages）

### 7. 追加の考慮事項 💭

1. **後方互換性**
   - 既存の設定や他のプロジェクトからの参照を壊さないよう、移行期間中は旧パスもサポート

2. **ドキュメント**
   - 新しい構造に合わせて README.md と DEVELOPER.md を更新

3. **CI/CD**
   - GitHub Actions などの設定を新しい構造に合わせて更新

4. **パフォーマンス**
   - 共通機能の抽出により、重複コードを削減し、メンテナンス性を向上

## まとめ ✨

このリファクタリングにより：
- 機能ごとに明確に分離されたモジュール構造
- Python コミュニティの標準に準拠した構造
- 統一されたテスト・リント・フォーマット環境
- 将来の拡張性とメンテナンス性の向上

次のセッションでこの計画に基づいて実装を進めていきます！