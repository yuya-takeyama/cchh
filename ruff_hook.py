#!/usr/bin/env python3
"""
Hook script to run ruff format on Python files after editing.
This hook is triggered by PostToolUse event.
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    # Hookデータを標準入力から読み込み
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # JSONパースエラーは無視（別のhookの可能性）
        sys.exit(0)

    # PostToolUse以外は無視
    event_type = hook_data.get("event_type", "")
    if event_type != "PostToolUse":
        sys.exit(0)

    # エラーが発生している場合は無視
    result = hook_data.get("result", {})
    if "error" in result or "exception" in result:
        sys.exit(0)

    # ツールの種類を確認
    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})

    # Edit, MultiEdit, WriteツールでPythonファイルを編集した場合のみ処理
    if tool_name not in ["Edit", "MultiEdit", "Write"]:
        sys.exit(0)

    # ファイルパスを取得
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Pythonファイルかどうか確認
    if not file_path.endswith(".py"):
        sys.exit(0)

    # ファイルが存在するか確認
    if not Path(file_path).exists():
        sys.exit(0)

    # ruff formatを実行
    try:
        # ruff format [file] を実行
        result = subprocess.run(
            ["ruff", "format", file_path], capture_output=True, text=True
        )

        # 成功した場合はメッセージを出力
        if result.returncode == 0:
            print(f"✨ Formatted {Path(file_path).name} with ruff", file=sys.stderr)
        else:
            # エラーがあれば出力
            if result.stderr:
                print(f"⚠️  Ruff format error: {result.stderr}", file=sys.stderr)

    except FileNotFoundError:
        print("⚠️  Ruff not found. Install with: uv tool install ruff", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Error running ruff: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
