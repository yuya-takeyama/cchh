"""Hook event handlers"""

import os
from typing import Any

from .config import NotificationLevel, ZundaspeakStyle
from .messages import (
    CRITICAL_COMMANDS,
    IMPORTANT_COMMANDS,
    IMPORTANT_NOTIFICATIONS,
    IMPORTANT_TASK_KEYWORDS,
    SLACK_MESSAGES,
    ZUNDAMON_MESSAGES,
)
from .notifiers import slack_notifier, zundaspeak_notifier
from .session import SessionManager
from .utils import (
    convert_command_to_readable,
    extract_permission_tool_name,
    format_cwd_for_slack,
    truncate_command,
)


class HookHandler:
    """Handle different hook events"""

    def __init__(self, session_id: str, cwd: str | None = None):
        self.session_id = session_id
        self.session_manager = SessionManager(session_id)
        self.cwd = cwd or os.getcwd()

    def handle_pre_tool_use(self, data: dict[str, Any]) -> None:
        """Handle PreToolUse event"""
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Prepare zundaspeak messages (whitelist approach)
        voice_message = None

        # Prepare Slack notifications with levels
        notifications: list[tuple[str, NotificationLevel]] = []

        if tool_name == "Task":
            description = tool_input.get("description", "")
            if description:
                voice_message = ZUNDAMON_MESSAGES["task_with_description"].format(
                    description=description
                )
                # 重要なタスクはチャンネル、その他はスレッド
                level = (
                    NotificationLevel.CHANNEL
                    if any(
                        keyword in description.lower()
                        for keyword in IMPORTANT_TASK_KEYWORDS
                    )
                    else NotificationLevel.THREAD
                )
                notifications.append(
                    (
                        SLACK_MESSAGES["task_start"].format(description=description),
                        level,
                    )
                )
            else:
                voice_message = ZUNDAMON_MESSAGES["task_execute"]
                notifications.append(
                    (SLACK_MESSAGES["task_start_simple"], NotificationLevel.THREAD)
                )

        elif tool_name == "Bash":
            cmd = tool_input.get("command", "")
            truncated_cmd = truncate_command(cmd)

            # 特定のコマンドは音声読み上げをスキップ
            silent_commands = ["git status", "git log", "git diff"]
            if any(
                cmd.strip().startswith(silent_cmd) for silent_cmd in silent_commands
            ):
                voice_message = None
            else:
                # Convert command to readable Japanese for speech (use original cmd, not truncated)
                readable_cmd = convert_command_to_readable(cmd)
                voice_message = ZUNDAMON_MESSAGES["bash_command"].format(
                    command=readable_cmd
                )

                # Debug log for voice synthesis (only in non-test environment)
                from .utils import is_test_environment

                if not is_test_environment():
                    import os

                    debug_log_path = os.path.join(os.getcwd(), "voice_debug.log")
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(f"Original: {repr(cmd)}\n")
                        f.write(f"Truncated: {repr(truncated_cmd)}\n")
                        f.write(f"Readable: {repr(readable_cmd)}\n")
                        f.write(f"Voice message: {repr(voice_message)}\n")
                        f.write("---\n")

            # 重要コマンドの分類
            if any(cmd.startswith(critical_cmd) for critical_cmd in CRITICAL_COMMANDS):
                notifications.append(
                    (
                        SLACK_MESSAGES["command_critical"].format(
                            command=truncated_cmd
                        ),
                        NotificationLevel.CHANNEL,
                    )
                )
            elif any(
                cmd.startswith(important_cmd) for important_cmd in IMPORTANT_COMMANDS
            ):
                notifications.append(
                    (
                        SLACK_MESSAGES["command_important"].format(
                            command=truncated_cmd
                        ),
                        NotificationLevel.THREAD,
                    )
                )

        elif tool_name == "TodoWrite":
            # TodoWrite は音声読み上げをスキップ
            voice_message = None
            # TodoWriteの内容も投稿
            todos = tool_input.get("todos", [])
            if todos:
                todo_lines = []
                for todo in todos[:5]:  # 最大5個まで
                    checkbox = (
                        ":white_check_mark:"
                        if todo.get("status") == "completed"
                        else ":ballot_box_with_check:"
                    )
                    todo_lines.append(f"{checkbox} {todo.get('content', '')}")
                todo_summary = "\n".join(todo_lines)
                formatted_message = SLACK_MESSAGES["todo_update_detail"].format(
                    todos=todo_summary
                )
                notifications.append((formatted_message, NotificationLevel.THREAD))
            else:
                notifications.append(
                    (SLACK_MESSAGES["todo_update"], NotificationLevel.THREAD)
                )

        elif tool_name in ["Write", "Edit", "MultiEdit"]:
            file_path = tool_input.get("file_path", "")
            if file_path:
                # cwdからの相対パスを計算
                try:
                    relative_path = os.path.relpath(file_path, self.cwd)
                except ValueError:
                    # 異なるドライブの場合など、相対パス計算できない場合は絶対パス
                    relative_path = file_path

                notifications.append(
                    (
                        SLACK_MESSAGES["file_operation"].format(
                            operation=tool_name.lower(), filename=relative_path
                        ),
                        NotificationLevel.THREAD,
                    )
                )

        # Send Slack notifications
        for message, level in notifications:
            slack_notifier.notify(
                message, level=level, session_manager=self.session_manager, cwd=self.cwd
            )

        # Only speak for whitelisted tools
        if voice_message:
            zundaspeak_notifier.notify(voice_message)

    def handle_post_tool_use(self, data: dict[str, Any]) -> None:
        """Handle PostToolUse event"""
        tool_name = data.get("tool_name", "")
        result = data.get("result", {})

        # エラーが発生した場合の通知（チャンネルレベル）
        if "error" in result or "exception" in result:
            error_msg = result.get("error", result.get("exception", "Unknown error"))
            slack_notifier.notify(
                SLACK_MESSAGES["tool_error"].format(
                    tool_name=tool_name, error=error_msg[:100]
                ),
                level=NotificationLevel.CHANNEL,
                session_manager=self.session_manager,
                cwd=self.cwd,
            )

        # 長時間実行されたTaskの完了通知（スレッドレベル）
        if tool_name == "Task":
            slack_notifier.notify(
                SLACK_MESSAGES["task_complete"].format(tool_name=tool_name),
                level=NotificationLevel.THREAD,
                session_manager=self.session_manager,
                cwd=self.cwd,
            )

    def handle_notification(self, data: dict[str, Any]) -> None:
        """Handle Notification event"""
        msg = data.get("message", "")

        # Skip file modification messages
        if any(word in msg.lower() for word in ["file", "modified", "change"]):
            return

        # Slack通知: 重要な通知のみ
        if any(keyword in msg.lower() for keyword in IMPORTANT_NOTIFICATIONS):
            if "error" in msg.lower() or "failed" in msg.lower():
                slack_notifier.notify(
                    SLACK_MESSAGES["notification_error"].format(message=msg),
                    level=NotificationLevel.CHANNEL,
                    session_manager=self.session_manager,
                    cwd=self.cwd,
                )
            elif "finished" in msg.lower() or "completed" in msg.lower():
                slack_notifier.notify(
                    SLACK_MESSAGES["notification_complete"].format(message=msg),
                    level=NotificationLevel.CHANNEL,
                    session_manager=self.session_manager,
                    cwd=self.cwd,
                )
            elif "permission" in msg.lower():
                # 許可要求はチャンネルに投稿して即座に気づけるようにする
                tool_name = extract_permission_tool_name(msg)
                permission_msg = (
                    SLACK_MESSAGES["notification_permission"].format(
                        tool_name=tool_name
                    )
                    if tool_name
                    else SLACK_MESSAGES["notification_permission_generic"].format(
                        message=msg
                    )
                )
                slack_notifier.notify(
                    permission_msg,
                    level=NotificationLevel.CHANNEL,
                    session_manager=self.session_manager,
                    broadcast=True,
                    cwd=self.cwd,
                )
            elif "waiting" in msg.lower():
                slack_notifier.notify(
                    SLACK_MESSAGES["notification_waiting"].format(message=msg),
                    level=NotificationLevel.THREAD,
                    session_manager=self.session_manager,
                    cwd=self.cwd,
                )

        # Translate message if available
        translated_msg = ZUNDAMON_MESSAGES.get(msg, msg)

        # Determine style based on message content
        style = ZundaspeakStyle.NORMAL.value  # default
        if "permission" in msg.lower() or "許可" in translated_msg:
            style = ZundaspeakStyle.AMAAMA.value
        elif "completed" in msg.lower() or "終わった" in translated_msg:
            style = ZundaspeakStyle.AMAAMA.value
        elif "waiting" in msg.lower() or "待ち" in translated_msg:
            style = ZundaspeakStyle.SEXY.value

        zundaspeak_notifier.notify(translated_msg, style=style)

    def handle_stop(self, data: dict[str, Any]) -> None:
        """Handle Stop event"""
        # セッション終了をSlackに通知（チャンネルレベル＋ブロードキャスト）
        slack_notifier.notify(
            SLACK_MESSAGES["session_end"],
            level=NotificationLevel.CHANNEL,
            session_manager=self.session_manager,
            broadcast=True,
            cwd=self.cwd,
        )

        zundaspeak_notifier.notify(
            ZUNDAMON_MESSAGES["session_end"], style=ZundaspeakStyle.SEXY.value
        )

    def handle_session_start(self) -> None:
        """Handle session start (called when new session detected)"""
        slack_notifier.notify(
            SLACK_MESSAGES["session_start"].format(
                session_id=self.session_id[:8], cwd=format_cwd_for_slack(self.cwd)
            ),
            level=NotificationLevel.CHANNEL,
            session_manager=self.session_manager,
            cwd=self.cwd,
        )

    def handle_user_prompt_submit(self, data: dict[str, Any]) -> None:
        """Handle UserPromptSubmit event"""
        prompt = data.get("prompt", "")

        if prompt:
            # エスケープされた改行を実際の改行に変換
            prompt = prompt.replace("\\n", "\n")

            # プロンプトをコードブロックで囲んで送信
            prompt_message = f"```\n{prompt}\n```"
            slack_notifier.notify(
                prompt_message,
                level=NotificationLevel.THREAD,
                session_manager=self.session_manager,
                broadcast=True,  # スレッドに投稿しても、チャンネルにも表示
                cwd=self.cwd,
            )
