"""Event message formatting for Slack"""

import os
from typing import Any

from .config import NotificationLevel

# Slack message templates
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
    "file_operation": "📝 ファイル{operation}: `{filename}`",
    # Web fetch messages
    "web_fetch": "🌐 Web取得: {url}",
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


class EventFormatter:
    """Formats hook events into Slack messages"""

    def __init__(self, session_id_length: int = 8):
        self.session_id_length = session_id_length

    def format_session_start(self, session_id: str, cwd: str) -> str:
        """Format session start message"""
        # セッションIDを設定された文字数に短縮
        short_session_id = (
            session_id[: self.session_id_length]
            if len(session_id) > self.session_id_length
            else session_id
        )
        return SLACK_MESSAGES["session_start"].format(
            session_id=short_session_id, cwd=self._format_cwd(cwd)
        )

    def format_task_start(
        self, description: str | None
    ) -> tuple[str, NotificationLevel]:
        """Format task start message with appropriate level"""
        if description:
            # 重要なタスクはチャンネル、その他はスレッド
            level = (
                NotificationLevel.CHANNEL
                if any(
                    keyword in description.lower()
                    for keyword in IMPORTANT_TASK_KEYWORDS
                )
                else NotificationLevel.THREAD
            )
            message = SLACK_MESSAGES["task_start"].format(description=description)
        else:
            level = NotificationLevel.THREAD
            message = SLACK_MESSAGES["task_start_simple"]

        return message, level

    def format_command(
        self, command: str
    ) -> tuple[str | None, NotificationLevel | None]:
        """Format command message with appropriate level"""
        # 重要コマンドの分類
        if any(command.startswith(critical_cmd) for critical_cmd in CRITICAL_COMMANDS):
            emoji = "🚨"
            level = NotificationLevel.CHANNEL
        elif any(
            command.startswith(important_cmd) for important_cmd in IMPORTANT_COMMANDS
        ):
            emoji = "⚡"
            level = NotificationLevel.THREAD
        else:
            # その他のコマンドもすべてスレッドレベルで通知
            emoji = "💻"
            level = NotificationLevel.THREAD

        # 複数行コマンドの場合はコードブロックで表示
        if "\n" in command:
            # コマンド内のバッククォートをエスケープ
            escaped_command = command.replace("```", "\\`\\`\\`")
            message = f"{emoji} コマンド実行\n```\n$ {escaped_command}\n```"
        else:
            message = f"{emoji} コマンド実行: `{command}`"

        return message, level

    def format_todo_update(
        self, todos: list[dict[str, Any]]
    ) -> tuple[str, NotificationLevel]:
        """Format todo update message"""
        if todos:
            todo_lines = []
            for todo in todos[:5]:  # 最大5個まで
                checkbox = (
                    SLACK_MESSAGES["todo_checkbox_completed"]
                    if todo.get("status") == "completed"
                    else SLACK_MESSAGES["todo_checkbox_pending"]
                )
                todo_lines.append(f"{checkbox} {todo.get('content', '')}")
            todo_summary = "\n".join(todo_lines)
            message = SLACK_MESSAGES["todo_update_detail"].format(todos=todo_summary)
        else:
            message = SLACK_MESSAGES["todo_update"]

        return message, NotificationLevel.THREAD

    def format_file_operation(
        self, tool_name: str, file_path: str, cwd: str
    ) -> tuple[str, NotificationLevel]:
        """Format file operation message"""
        # cwdからの相対パスを計算
        try:
            relative_path = os.path.relpath(file_path, cwd)
        except ValueError:
            # 異なるドライブの場合など、相対パス計算できない場合は絶対パス
            relative_path = file_path

        # 操作名を日本語に変換
        operation_map = {
            "Edit": "編集",
            "Write": "作成",
            "MultiEdit": "編集",
        }
        operation = operation_map.get(tool_name, tool_name.lower())

        message = SLACK_MESSAGES["file_operation"].format(
            operation=operation, filename=relative_path
        )
        return message, NotificationLevel.THREAD

    def format_web_fetch(self, url: str) -> tuple[str, NotificationLevel]:
        """Format web fetch message"""
        message = SLACK_MESSAGES["web_fetch"].format(url=url)
        return message, NotificationLevel.THREAD

    def format_tool_error(
        self, tool_name: str, error: str
    ) -> tuple[str, NotificationLevel]:
        """Format tool error message"""
        message = SLACK_MESSAGES["tool_error"].format(
            tool_name=tool_name, error=error[:100]
        )
        return message, NotificationLevel.CHANNEL

    def format_notification(
        self, notification: dict[str, Any] | str
    ) -> tuple[str, NotificationLevel]:
        """Format notification message"""
        # Handle both string and dict notification formats
        if isinstance(notification, str):
            text = notification
        else:
            # Handle structured permission request format
            if notification.get("type") == "toolUseRequiresApproval":
                tool_name = notification.get("tool", "Unknown")
                message = SLACK_MESSAGES["notification_permission"].format(
                    tool_name=tool_name
                )
                return message, NotificationLevel.CHANNEL
            
            text = notification.get("text", "")

        # 重要な通知の判定
        is_important = any(
            keyword in text.lower() for keyword in IMPORTANT_NOTIFICATIONS
        )

        # メッセージタイプに応じたフォーマット
        if "error" in text.lower() or "failed" in text.lower():
            message = SLACK_MESSAGES["notification_error"].format(message=text)
        elif (
            "completed successfully" in text.lower()
            or "claude has finished" in text.lower()
        ):
            message = SLACK_MESSAGES["notification_complete"].format(message=text)
        elif "claude needs your permission" in text.lower():
            # Extract tool name from permission message
            tool_name = self._extract_permission_tool_name(text)
            if tool_name:
                message = SLACK_MESSAGES["notification_permission"].format(
                    tool_name=tool_name
                )
            else:
                message = SLACK_MESSAGES["notification_permission_generic"].format(
                    message=text
                )
        elif "claude is waiting for your input" in text.lower():
            message = SLACK_MESSAGES["notification_waiting"].format(message=text)
        else:
            message = f"ℹ️ {text}"

        level = NotificationLevel.CHANNEL if is_important else NotificationLevel.THREAD
        return message, level

    def format_user_prompt(self, prompt: str) -> str:
        """Format user prompt for display"""
        # エスケープされた改行を実際の改行に変換
        prompt = prompt.replace("\\n", "\n")
        # プロンプトをコードブロックで囲む
        return f"```\n{prompt}\n```"

    def _format_cwd(self, cwd: str) -> str:
        """Format cwd for Slack display"""
        home = str(os.path.expanduser("~"))

        # まず ~/src/github.com/ のプレフィックスを削除
        github_prefix = os.path.join(home, "src", "github.com", "")
        if cwd.startswith(github_prefix):
            return cwd[len(github_prefix) :]

        # それ以外の場合は $HOME を ~ に置き換え
        if cwd.startswith(home):
            return cwd.replace(home, "~", 1)

        return cwd

    def _extract_permission_tool_name(self, text: str) -> str | None:
        """Extract tool name from permission message"""
        if "Claude needs your permission to use" in text:
            parts = text.split("Claude needs your permission to use")
            if len(parts) > 1:
                return parts[1].strip().split()[0]
        return None
