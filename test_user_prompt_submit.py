#!/usr/bin/env python3
"""Test script for UserPromptSubmit hook"""

import json
import subprocess
import sys

# テスト用のUserPromptSubmitイベント
test_event = {
    "timestamp": "2025-07-20T10:21:39.633704Z",
    "hook_event_name": "UserPromptSubmit",
    "data": {
        "session_id": "test-session-123",
        "transcript_path": "/Users/yuya/.claude/projects/test/test-session-123.jsonl",
        "cwd": "/Users/yuya/test-project",
        "prompt": "@src/index.ts @package.json\\nこのツールを使って、Notion から Dify にデータを同期したい。\\n\\nDify API の情報は以下です。\\n\\nlocalhost に立てたテスト環境なので雑に伝えます。\\n\\nAPI Server: http://localhost/v1\\nAPI Key: dataset-EgJdUbPvkuyGcIcpWQehoFZ8\\n\\nこの情報を使って dok でのデータベースの登録をやってみてください。\\n\\nNotion 周りの情報は環境変数に入ってます。\\n\\nthink harder",
    },
    "session_id": "test-session-123",
}

# hook_handler.pyを実行
result = subprocess.run(
    [sys.executable, "/Users/yuya/.claude/scripts/hook_handler.py"],
    input=json.dumps(test_event),
    capture_output=True,
    text=True,
)

print("=== Output ===")
print(result.stdout)

if result.stderr:
    print("\n=== Error ===")
    print(result.stderr)

print(f"\n=== Exit code: {result.returncode} ===")
