"""Slack notification handler"""

import json
import sys
import urllib.parse
import urllib.request

from ..core.base import BaseHandler
from ..core.types import HookEvent, HookEventName
from ..utils.logger import get_error_logger
from .command_formatter import CommandFormatter
from .config import NotificationLevel, RuntimeConfig
from .event_formatter import EventFormatter
from .session_tracker import SlackSessionTracker


class SlackNotifier(BaseHandler):
    """Handles Slack notifications for Claude Code events"""

    def __init__(self, config: RuntimeConfig | None = None):
        self.config = config or RuntimeConfig.from_environment()
        self.api_url = "https://slack.com/api/chat.postMessage"
        self.event_formatter = EventFormatter(
            session_id_length=self.config.session_id_length
        )
        self.command_formatter = CommandFormatter()
        self.error_logger = get_error_logger()
        self._session_trackers: dict[
            str, SlackSessionTracker
        ] = {}  # Cache session trackers

        # Ensure thread directory exists
        if self.config.is_configured:
            self.config.thread_dir.mkdir(parents=True, exist_ok=True)

    def handle_event(self, event: HookEvent) -> None:
        """Handle incoming hook event"""
        if not self.should_handle_event(event):
            return

        # Get or create session tracker
        session_tracker = self._get_session_tracker(event.session_id)

        # Check for new session
        if session_tracker.is_new_session and self.config.show_session_start:
            self._handle_session_start(event, session_tracker)

        # Handle specific event types
        if (
            event.hook_event_name in (HookEventName.PRE_TOOL_USE, "PreToolUse")
            and self.config.notify_on_tool_use
        ):
            self._handle_pre_tool_use(event, session_tracker)
        elif event.hook_event_name in (HookEventName.POST_TOOL_USE, "PostToolUse"):
            self._handle_post_tool_use(event, session_tracker)
        elif event.hook_event_name in (HookEventName.NOTIFICATION, "Notification"):
            self._handle_notification(event, session_tracker)
        elif (
            event.hook_event_name in (HookEventName.STOP, "Stop")
            and self.config.notify_on_stop
        ):
            self._handle_stop(event, session_tracker)
        elif event.hook_event_name in (
            HookEventName.USER_PROMPT_SUBMIT,
            "UserPromptSubmit",
        ):
            self._handle_user_prompt_submit(event, session_tracker)
        elif event.hook_event_name in (HookEventName.PRE_COMPACT, "PreCompact"):
            self._handle_pre_compact(event, session_tracker)

    def _handle_session_start(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle new session start"""
        message = self.event_formatter.format_session_start(event.session_id, event.cwd)
        self._send_notification(
            message, NotificationLevel.CHANNEL, session_tracker, event.cwd
        )

    def _handle_pre_tool_use(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle PreToolUse event"""
        if not event.tool_name or not event.tool_input:
            return

        notifications = []

        if event.tool_name == "Task":
            description = event.tool_input.get("description", "")
            message, level = self.event_formatter.format_task_start(description)
            if message:
                notifications.append((message, level))

        elif event.tool_name == "Bash":
            cmd = event.tool_input.get("command", "")
            if cmd:
                # Format command (no silent commands filtering for Slack)
                truncated_cmd = self.command_formatter.format(cmd)
                result = self.event_formatter.format_command(truncated_cmd)
                if result[0] is not None and result[1] is not None:
                    notifications.append((result[0], result[1]))

        elif event.tool_name == "TodoWrite":
            todos = event.tool_input.get("todos", [])
            message, level = self.event_formatter.format_todo_update(todos)
            notifications.append((message, level))

        elif event.tool_name in ["Write", "Edit", "MultiEdit"]:
            file_path = event.tool_input.get("file_path", "")
            if file_path:
                message, level = self.event_formatter.format_file_operation(
                    event.tool_name, file_path, event.cwd
                )
                notifications.append((message, level))

        elif event.tool_name == "WebFetch":
            url = event.tool_input.get("url", "")
            if url:
                message, level = self.event_formatter.format_web_fetch(url)
                notifications.append((message, level))

        # Send all notifications
        for message, level in notifications:
            self._send_notification(message, level, session_tracker, event.cwd)

    def _handle_post_tool_use(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle PostToolUse event"""
        if not event.tool_name or not event.result:
            return

        # エラーが発生した場合の通知
        if "error" in event.result or "exception" in event.result:
            error_msg = event.result.get(
                "error", event.result.get("exception", "Unknown error")
            )
            message, level = self.event_formatter.format_tool_error(
                event.tool_name, error_msg
            )
            self._send_notification(message, level, session_tracker, event.cwd)

        # 長時間実行されたTaskの完了通知
        elif event.tool_name == "Task":
            message = f"✅ タスク完了: {event.tool_name}"
            self._send_notification(
                message, NotificationLevel.THREAD, session_tracker, event.cwd
            )

    def _handle_notification(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle Notification event"""
        if not event.notification:
            return

        message, level = self.event_formatter.format_notification(event.notification)
        self._send_notification(message, level, session_tracker, event.cwd)

    def _handle_stop(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle Stop event"""
        message = "🛑 Claude Codeセッション終了"
        self._send_notification(
            message,
            NotificationLevel.THREAD,
            session_tracker,
            event.cwd,
            broadcast=True,
        )

    def _handle_user_prompt_submit(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle UserPromptSubmit event"""
        if not event.prompt:
            return

        message = self.event_formatter.format_user_prompt(event.prompt)
        self._send_notification(
            message,
            NotificationLevel.THREAD,
            session_tracker,
            event.cwd,
            broadcast=True,
        )

    def _handle_pre_compact(
        self, event: HookEvent, session_tracker: SlackSessionTracker
    ) -> None:
        """Handle PreCompact event"""
        message = "⚠️ コンテキストが長くなってきました。新しいセッションの開始を検討してください。"
        self._send_notification(
            message,
            NotificationLevel.THREAD,
            session_tracker,
            event.cwd,
            broadcast=True,
        )

    def _send_notification(
        self,
        message: str,
        level: NotificationLevel,
        session_tracker: SlackSessionTracker,
        cwd: str,
        broadcast: bool = False,
    ) -> str | None:
        """Send notification to Slack"""
        # Load thread state
        thread_state = self._load_thread_state(session_tracker.session_id)
        is_new_thread = not thread_state or not thread_state.get("thread_ts")

        data = {
            "channel": self.config.channel_id,
            "text": message,
            "username": "Claude Code Bot",
            "icon_emoji": ":robot_face:",
        }

        # 重要なメッセージはbroadcastする
        if broadcast:
            data["reply_broadcast"] = "true"

        if level == NotificationLevel.CHANNEL:
            # チャンネル投稿時：スレッドを新規作成または既存を使用
            if thread_state and thread_state.get("thread_ts"):
                # 既存スレッドがある場合は返信として投稿
                data["thread_ts"] = thread_state["thread_ts"]

        elif level == NotificationLevel.THREAD:
            # スレッド投稿時：既存スレッドに投稿、なければチャンネル投稿でスレッド作成
            if thread_state and thread_state.get("thread_ts"):
                data["thread_ts"] = thread_state["thread_ts"]

        headers = {
            "Authorization": f"Bearer {self.config.bot_token}",
            "Content-Type": "application/json",
        }

        try:
            req = urllib.request.Request(
                self.api_url, data=json.dumps(data).encode("utf-8"), headers=headers
            )

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("ok"):
                    # 投稿成功時、スレッドTSを保存
                    message_ts = result.get("ts")

                    # 新規スレッド作成の場合（thread_tsが設定されていない投稿）
                    if message_ts and is_new_thread:
                        self._save_thread_state(session_tracker.session_id, message_ts)

                    return message_ts
                else:
                    # エラーログ出力
                    print(
                        f"Slack notification failed: {result.get('error', 'Unknown error')}",
                        file=sys.stderr,
                    )

                    # Log to error file
                    self.error_logger.log_error(
                        error_type="slack_api_error",
                        error_message=f"Slack API error: {result.get('error', 'Unknown error')}",
                        context={
                            "channel": self.config.channel_id,
                            "message_preview": message[:100] if message else "",
                            "level": level.value,
                            "thread_ts": data.get("thread_ts"),
                            "response": result,
                        },
                    )
                    return None

        except Exception as e:
            # 通知失敗してもメイン処理は止めない
            print(f"Slack notification error: {e}", file=sys.stderr)

            # Log to error file
            self.error_logger.log_error(
                error_type="slack_notification_error",
                error_message=str(e),
                context={
                    "channel": self.config.channel_id,
                    "message_preview": message[:100] if message else "",
                    "level": level.value,
                },
                exception=e,
            )
            return None

    def _get_session_tracker(self, session_id: str) -> SlackSessionTracker:
        """Get or create session tracker for the session"""
        if session_id not in self._session_trackers:
            self._session_trackers[session_id] = SlackSessionTracker(session_id)
        return self._session_trackers[session_id]

    def _load_thread_state(self, session_id: str) -> dict | None:
        """Load thread state for session"""
        thread_file = self.config.thread_dir / f"{session_id}.json"
        if thread_file.exists():
            try:
                return json.loads(thread_file.read_text())
            except Exception:
                return None
        return None

    def _save_thread_state(self, session_id: str, thread_ts: str) -> None:
        """Save thread state for session"""
        thread_file = self.config.thread_dir / f"{session_id}.json"
        thread_state = {"thread_ts": thread_ts}
        try:
            thread_file.write_text(json.dumps(thread_state))
        except Exception as e:
            print(f"Failed to save thread state: {e}", file=sys.stderr)

    def should_handle_event(self, event: HookEvent) -> bool:
        """イベントを処理すべきか判定する純粋関数"""
        if not self.config.notifications_enabled:
            return False
        if not self.config.is_configured:
            return False
        if self.config.is_test_environment:
            return False
        return True
