#!/bin/bash

# イベントログ記録スクリプト
# cwdとイベントJSONをJSONL形式でログファイルに追記

LOG_FILE="$HOME/.claude/event_logs.json"

# 標準入力からイベントJSONを読み取り、cwdと組み合わせてJSONL形式で出力
jq -c --arg cwd "$PWD" '{cwd: $cwd, event: .}' >> "$LOG_FILE"