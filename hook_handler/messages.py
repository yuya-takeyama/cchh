"""Message translations and templates"""

ZUNDAMON_MESSAGES: dict[str, str] = {
    # Task messages
    "task_execute": "タスク実行するのだ",
    "task_with_description": "タスク「{description}」を実行するのだ",
    # Bash command messages
    "bash_command": "コマンド『{command}』発射するのだ",
    # TodoWrite messages
    "todo_write": "To Doを書き込むのだ",
    # Notification translations
    "Claude needs your permission to use Bash": "コマンドの許可が欲しいのだ",
    "Claude needs your permission to use Task": "タスク実行の許可が欲しいのだ",
    "Claude needs your permission to use Read": "ファイル読み込みの許可が欲しいのだ",
    "Claude needs your permission to use Write": "ファイル書き込みの許可が欲しいのだ",
    "Claude needs your permission to use Edit": "ファイル編集の許可が欲しいのだ",
    "Claude needs your permission to use MultiEdit": "ファイル編集の許可が欲しいのだ",
    "Claude needs your permission to use TodoWrite": "TODO更新の許可が欲しいのだ",
    "Claude needs your permission to use WebSearch": "Web検索の許可が欲しいのだ",
    "Claude needs your permission to use WebFetch": "Webアクセスの許可が欲しいのだ",
    "Claude needs your permission to use Grep": "ファイル検索の許可が欲しいのだ",
    "Claude needs your permission to use Glob": "ファイル探索の許可が欲しいのだ",
    "Claude needs your permission to use LS": "フォルダ閲覧の許可が欲しいのだ",
    "Claude is waiting for your input": "入力待ちなのだ。何か指示が欲しいのだ",
    "Claude is thinking": "考え中なのだ。少し待つのだ",
    "Claude has finished": "終わったのだ",
    # Stop message
    "session_end": "作業が終わったのだ。次は何をするのだ？",
}

SLACK_MESSAGES = {
    # Session messages
    "session_start": ":clapper: `{session_id}` `{cwd}`",
    "session_end": "🛑 Claude Codeセッション終了",
    # Task messages
    "task_start": "🔧 タスク開始: {description}",
    "task_start_simple": "🔧 タスク開始",
    "task_complete": "✅ タスク完了: {tool_name}",
    # Command messages
    "command_critical": "🚨 重要コマンド実行: `{command}`",
    "command_important": "⚡ コマンド実行: `{command}`",
    # File operation messages
    "file_operation": "📝 ファイル{operation}: {filename}",
    # Todo messages
    "todo_update": "📋 TODO更新",
    "todo_update_detail": "---\n📋 TODO更新:\n{todos}\n---",
    "todo_checkbox_completed": ":white_check_mark:",
    "todo_checkbox_pending": ":ballot_box_with_check:",
    # Error messages
    "tool_error": "❌ {tool_name} エラー: {error}...",
    # Notification messages
    "notification_error": "⚠️ 通知: {message}",
    "notification_complete": "✅ {message}",
    "notification_permission": "🔐 許可要求: {tool_name}ツールの使用許可",
    "notification_permission_generic": "🔐 許可要求: {message}",
    "notification_waiting": "⏱️ {message}",
}


# Critical commands that should be notified at channel level
CRITICAL_COMMANDS = ["git commit", "git push", "npm publish", "docker push"]

# Important commands that should be notified at thread level
IMPORTANT_COMMANDS = ["git", "npm", "pnpm", "docker", "kubectl", "terraform"]

# Keywords that indicate important tasks
IMPORTANT_TASK_KEYWORDS = ["エラー", "修正", "実装", "バグ", "fix", "bug", "implement"]

# Important notification keywords
IMPORTANT_NOTIFICATIONS = [
    "claude has finished",
    "claude is waiting for your input",
    "claude needs your permission",
    "error",
    "failed",
    "completed successfully",
]
