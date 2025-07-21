# CCHH - Claude Code Hook Handlers

[![test](https://github.com/yuya-takeyama/cchh/actions/workflows/test.yaml/badge.svg)](https://github.com/yuya-takeyama/cchh/actions/workflows/test.yaml)

Claude Codeのhookイベントをハンドリングして、SlackとZundaspeakで通知を行うツールです。

## 機能

- **Slack通知**: ツール実行、エラー、セッション管理をSlackに通知
- **Zundaspeak音声通知**: 重要なイベントをずんだもんボイスで通知
- **セッション管理**: セッションごとにSlackスレッドを管理
- **ログ記録**: すべてのhookイベントをログファイルに記録

## インストールと使用方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/yuya-takeyama/cchh.git
cd cchh
```

### 2. 依存関係のインストール

```bash
# uvがインストールされていない場合
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係をインストール
uv sync
```

### 3. Claude Codeでの設定

Claude Codeの設定ファイル（~/.claude/settings.json または settings.local.json）に以下を追加：

```json
{
  "hooks": {
    "preToolUse": "cd /path/to/cchh && uv run python all_hooks.py",
    "postToolUse": [
      "cd /path/to/cchh && uv run python all_hooks.py",
      "cd /path/to/cchh && uv run python ruff_hook.py"
    ],
    "notification": "cd /path/to/cchh && uv run python all_hooks.py",
    "stop": "cd /path/to/cchh && uv run python all_hooks.py",
    "userPromptSubmit": "cd /path/to/cchh && uv run python all_hooks.py"
  }
}
```

注意：
- `postToolUse`では、エラー通知（all_hooks.py）とRuffフォーマット（ruff_hook.py）の両方を実行します
- Ruffフォーマットが不要な場合は、`ruff_hook.py`の行を削除してください

### 4. 環境変数の設定

Slack通知を使用する場合は、以下の環境変数を設定：

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_CHANNEL_ID="C0123456789"
```

## ディレクトリ構造

```
.
├── all_hooks.py                 # メインエントリーポイント（全イベント処理）
├── ruff_hook.py                 # Ruffフォーマット専用フック
├── hook_handler.py              # エントリーポイント（後方互換性用）
├── src/                         # 新しいモジュール構造
│   ├── __init__.py
│   ├── core/                    # コア機能
│   │   ├── __init__.py
│   │   ├── dispatcher.py        # イベントディスパッチャー
│   │   └── types.py             # 型定義
│   ├── slack/                   # Slack通知機能
│   │   ├── __init__.py
│   │   ├── notifier.py          # Slack通知メイン
│   │   ├── session_tracker.py   # セッション管理
│   │   ├── event_formatter.py   # イベントメッセージ整形
│   │   ├── command_formatter.py # コマンド整形
│   │   └── config.py            # Slack設定
│   ├── zunda/                   # ずんだもん音声機能
│   │   ├── __init__.py
│   │   ├── speaker.py           # 音声読み上げメイン
│   │   ├── prompt_formatter.py  # プロンプト整形
│   │   ├── command_formatter.py # コマンド整形（音声用）
│   │   └── config.py            # ずんだもん設定
│   ├── logger/                  # イベントロギング
│   │   ├── __init__.py
│   │   ├── event_logger.py      # JSONLロガー
│   │   └── config.py            # ロガー設定
│   └── utils/                   # 共通ユーティリティ
│       ├── __init__.py
│       ├── command_parser.py    # コマンド解析
│       ├── text_utils.py        # テキスト処理
│       ├── config.py            # 共通設定
│       ├── logger.py            # デバッグロガー
│       └── io_helpers.py        # I/Oヘルパー
├── hook_handler/                # 既存パッケージ（後方互換性）
├── tests/                       # テストディレクトリ
├── pyproject.toml               # プロジェクト設定
├── aqua/                        # aqua設定（ツール管理）
│   ├── aqua.yaml
│   └── aqua-checksums.json
└── .github/
    └── workflows/
        └── test.yaml            # CI/CD設定
```

## 設定

### 環境変数

#### Slack通知設定
- `SLACK_BOT_TOKEN`: Slack Bot Token (xoxb-...)
- `SLACK_CHANNEL_ID`: 通知先のSlackチャンネルID
- `SLACK_NOTIFICATIONS_ENABLED`: Slack通知全体のON/OFF (デフォルト: true)
- `SLACK_SHOW_SESSION_START`: セッション開始時のcwd表示 (デフォルト: true)
- `SLACK_NOTIFY_ON_TOOL_USE`: ツール使用時の通知 (デフォルト: true)
- `SLACK_NOTIFY_ON_STOP`: 処理終了時の通知 (デフォルト: true)
- `SLACK_COMMAND_MAX_LENGTH`: コマンド表示の最大文字数 (デフォルト: 200)

#### ずんだもん音声設定
- `ZUNDA_SPEAKER_ENABLED`: ずんだもん音声全体のON/OFF (デフォルト: true)
- `ZUNDA_SPEAK_ON_PROMPT_SUBMIT`: プロンプト送信時の読み上げ (デフォルト: true)
- `ZUNDA_SPEAK_SPEED`: 読み上げ速度 (デフォルト: 1.2)

#### イベントロギング設定
- `EVENT_LOGGING_ENABLED`: イベントロギングのON/OFF (デフォルト: true)
- `LOG_MAX_SIZE_MB`: ログファイルの最大サイズ（MB） (デフォルト: 100)
- `LOG_ROTATION_COUNT`: ログローテーション数 (デフォルト: 5)

#### その他
- `TEST_ENVIRONMENT`: テスト環境フラグ（テスト時は通知を送信しない）

## 開発

### 開発環境のセットアップ

```bash
# 依存関係のインストール
uv sync

# または開発タスクを実行
uv run task dev
```

### 利用可能なタスク

```bash
# テストの実行
uv run task test

# Lintの実行
uv run task lint

# コードフォーマット
uv run task format

# 型チェック
uv run task typecheck

# すべてのチェック（lint + test + typecheck）
uv run task all

# キャッシュとビルド成果物のクリーンアップ
uv run task clean
```

### テスト実行

```bash
# すべてのテストを実行（推奨）
uv run task test

# 特定のテストモジュールを実行
uv run pytest hook_handler/tests/test_utils.py -v

# 特定のテストクラスを実行
uv run pytest hook_handler/tests/test_handlers.py::TestHookHandler -v

# カバレッジレポート付きでテスト実行
uv run pytest --cov=hook_handler --cov-report=term-missing
```

## 主な改善点

1. **モジュール化**: 単一ファイルから機能別モジュールに分割
2. **テスタビリティ**: 依存性注入とモック化でテストしやすい構造に
3. **エラーハンドリング**: 適切なエラーハンドリングとロギング
4. **設定の外部化**: 設定値を一箇所で管理
5. **型安全性**: 型ヒントをサポート（py.typedファイル付き）

## コマンド変換ルールのカスタマイズ

Zundaspeak音声通知で読み上げるコマンドの変換ルールをカスタマイズできます。

### 変更可能なルール

#### 1. 単語の置換辞書 (`hook_handler/command_converter.py`)

プログラム名とサブコマンドの読み替えを定義：

```python
self.words = {
    # 完全一致コマンド
    "pwd": "ピーダブルディー",

    # プログラム名
    "git": "ギット",
    "npm": "エヌピーエム",
    "docker": "docker",  # 例: 新しいプログラム追加

    # サブコマンド
    "fetch": "フェッチ",
    "push": "プッシュ",
    "build": "ビルド",  # 例: 新しいサブコマンド追加
}
```

#### 2. 読み上げ部品数の制限 (`hook_handler/command_converter.py`)

コマンドの何部品目まで読み上げるかを指定：

```python
self.parts_limit = {
    # 2部品まで読む（3部品目以降は無視）
    "git fetch": 2,    # git fetch origin → ギット フェッチ
    "git push": 2,     # git push origin main → ギット プッシュ
    "npm run": 2,      # npm run test:unit → エヌピーエム ラン

    # 3部品以上読む特殊パターン
    "uv run task": 4,  # uv run task format → ユーブイ ラン タスク フォーマット
    "gh pr": 3,        # gh pr create → gh pr create
}
```

### デフォルトの動作

- `parts_limit` で明示的に指定された場合: その部品数まで読む
- それ以外の場合: 1部品（コマンド名）のみ読む

### 変換例

| コマンド                | 変換後                            |
| ----------------------- | --------------------------------- |
| `git fetch origin`      | ギット フェッチ                   |
| `npm install`           | エヌピーエム インストール         |
| `docker run -it ubuntu` | docker ラン                       |
| `uv run task format`    | ユーブイ ラン タスク フォーマット |

## その他のツール

### テストヘルパースクリプト

- **test_hook_handler.py**: hook_handler.pyのテスト実行用スクリプト
- **test_cwd_display.py**: 現在のディレクトリ表示のテスト
- **test_user_prompt_submit.py**: ユーザープロンプト送信のテスト
- **ruff_format_hook.py**: Ruffフォーマッターのhook実装例

### ログツール

- **event_logger.sh**: イベントをJSONL形式でログに記録するシェルスクリプト

## Documentation

- [Developer Guide](DEVELOPER.md) - Detailed technical documentation for contributors

## License

MIT License - see the [LICENSE](LICENSE) file for details.
