# Documentation Problems Report

## 調査日: 2025-07-21

このファイルは、README.md と CLAUDE.md のドキュメントと実際のコードベースの間の不一致を調査した結果をまとめたものです。

## 1. ディレクトリパスの不一致

### 問題
CLAUDE.md で記載されているログファイルのパスが実装と異なる

### 詳細
| ドキュメント記載 (CLAUDE.md) | 実装 | 該当ファイル |
|---------------------------|------|------------|
| `~/.claude/hooks.log` | `~/.cchh/logs/events.jsonl` | `src/logger/config.py:18` |
| `~/.claude/cchh_errors.log` | `~/.cchh/errors.log` | `src/utils/logger.py:16` |
| `~/.claude/slack_thread_ts/` | `~/.cchh/slack_threads/` | `src/slack/config.py:31` |
| (未記載) | `~/.cchh/sessions/` | `src/slack/session_tracker.py:18` |

### 対応方針
`.cchh` を正として、ドキュメントを修正する

## 2. 存在しないイベントタイプの記載

### 問題
CLAUDE.md に実装されていないイベントタイプが記載されている

### 詳細
- `SubagentStop` - CLAUDE.md line 147 に記載があるが、実装には存在しない
- `PreCompact` - CLAUDE.md line 148 に記載があるが、実装には存在しない

実際に実装されているイベントタイプ (`src/core/types.py`):
- `PRE_TOOL_USE`
- `POST_TOOL_USE`
- `NOTIFICATION`
- `STOP`
- `USER_PROMPT_SUBMIT`

## 3. README.md の hook 設定が不完全

### 問題
README.md では 5 つのサポートされているイベントタイプのうち 2 つしか記載されていない

### 詳細
- README.md に記載: `PreToolUse`, `PostToolUse` のみ
- 実際にサポート: `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `UserPromptSubmit`

## 4. プロジェクト構造の不一致

### 問題
CLAUDE.md に記載されているディレクトリ/ファイルで実在しないもの

### 詳細
- `tests/utils/` ディレクトリ - CLAUDE.md に記載があるが存在しない
- `test_*.py` (ルートレベルのヘルパーテストスクリプト) - 記載があるが存在しない

### ドキュメントに記載がないが存在するファイル
- `LICENSE`
- `.gitignore`
- `.claude/settings.local.json`
- `test_problems.md`
- `tests/conftest.py` (pytest 設定ファイル)

## 5. README.md の環境変数ドキュメント不足

### 問題
README.md には最小限の環境変数しか記載されていない

### 詳細
README.md に記載:
- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL_ID`

実際に利用可能な環境変数（CLAUDE.md には記載あり）:
- Slack 関連: 7 個
- Zunda 関連: 3 個
- ログ関連: 3 個
- その他: 1 個

## 6. その他の細かい問題

### CLAUDE.md の PostToolUse 設定
PostToolUse で `ruff_hook.py` も実行されることが記載されているが、README.md には記載なし

### 開発コマンドの不足（README.md）
- `uv run task all` コマンドが記載されていない
- `uv run task clean` コマンドが記載されていない

### Python バージョン要件
README.md に Python 3.13+ の要件が記載されていない

## 修正優先度

1. **高**: ディレクトリパスの統一（CLAUDE.md の修正）
2. **高**: 存在しないイベントタイプの削除（CLAUDE.md の修正）
3. **中**: README.md の hook 設定を完全にする
4. **中**: README.md に環境変数セクションを追加
5. **低**: プロジェクト構造の細かい不一致を修正
6. **低**: 開発コマンドの追加