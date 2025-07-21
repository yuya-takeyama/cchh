#!/usr/bin/env python3
"""Test script for cwd display formatting"""

import json
import os
import subprocess
import sys

# テスト用のセッション開始イベント（新しいセッションをシミュレート）
test_event = {
    "timestamp": "2025-07-20T12:00:00.000000Z",
    "hook_event_name": "PreToolUse",  # セッション開始のトリガー
    "data": {"tool_name": "Task", "tool_input": {"description": "Test task"}},
    "session_id": "test-cwd-display-123",
}

# 様々なcwdパターンをテスト
test_cwds = [
    "/Users/yuya/.claude/scripts",
    "/Users/yuya/projects/myapp",
    "/Users/yuya",
    "/tmp",
    "/usr/local/bin",
    "/var/log",
]

print("=== Testing cwd display formatting ===\n")

for cwd in test_cwds:
    print(f"Testing cwd: {cwd}")

    # cwdを含むイベントデータを作成
    test_event["cwd"] = cwd

    # 環境変数を設定してhook_handlerを実行
    env = os.environ.copy()
    env["TEST_ENVIRONMENT"] = "1"  # テスト環境フラグを設定

    result = subprocess.run(
        [sys.executable, "/Users/yuya/.claude/scripts/hook_handler.py"],
        input=json.dumps(test_event),
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode == 0:
        print("✓ Success")
    else:
        print(f"✗ Failed with exit code: {result.returncode}")
        if result.stderr:
            print(f"  Error: {result.stderr}")

    print("")

print("\n=== Expected results ===")
print("/Users/yuya/.claude/scripts -> .claude/scripts")
print("/Users/yuya/projects/myapp -> projects/myapp")
print("/Users/yuya -> ~")
print("/tmp -> /tmp")
print("/usr/local/bin -> /usr/local/bin")
print("/var/log -> /var/log")
