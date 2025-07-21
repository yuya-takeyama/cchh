# Claude Code Hook Handler

Claude Codeのhookイベントをハンドリングして、SlackとZundaspeakで通知を行うツールです。

## 機能

- **Slack通知**: ツール実行、エラー、セッション管理をSlackに通知
- **Zundaspeak音声通知**: 重要なイベントをずんだもんボイスで通知
- **セッション管理**: セッションごとにSlackスレッドを管理
- **ログ記録**: すべてのhookイベントをログファイルに記録

## ディレクトリ構造

```
scripts/
├── hook_handler.py              # エントリーポイント（後方互換性用）
├── test_hook_handler.py         # テストランナー
└── hook_handler/               # メインパッケージ
    ├── __init__.py
    ├── main.py                  # メインエントリーポイント
    ├── config.py                # 設定管理
    ├── messages.py              # メッセージテンプレート
    ├── command_converter.py     # コマンド変換ロジック
    ├── utils.py                 # ユーティリティ関数
    ├── session.py               # セッション管理
    ├── notifiers.py             # 通知ハンドラー（Slack/Zundaspeak）
    ├── handlers.py              # Hookイベントハンドラー
    ├── logger.py                # ロギング
    └── tests/                   # テストスイート
        ├── __init__.py
        ├── test_command_converter.py
        ├── test_utils.py
        ├── test_session.py
        ├── test_notifiers.py
        └── test_handlers.py
```

## 設定

環境変数で設定：

- `SLACK_BOT_TOKEN`: Slack Bot Token (xoxb-...)
- `SLACK_CHANNEL_ID`: 通知先のSlackチャンネルID
- `SLACK_ENABLED`: Slack通知の有効/無効 (デフォルト: 1)
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
uv run pytest scripts/hook_handler/tests/test_utils.py -v

# 特定のテストクラスを実行
uv run pytest scripts/hook_handler/tests/test_handlers.py::TestHookHandler -v

# カバレッジレポート付きでテスト実行
uv run pytest --cov=scripts/hook_handler --cov-report=term-missing
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
