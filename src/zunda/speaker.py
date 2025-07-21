"""Zunda speaker handler"""

import os
import subprocess

from ..core.base import BaseHandler
from ..core.types import HookEvent, HookEventName
from ..utils.logger import get_error_logger
from .command_formatter import CommandFormatter
from .config import zunda_config

# Zundamon message templates
ZUNDAMON_MESSAGES = {
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
    # PreCompact message
    "pre_compact": "コンテキストが長くなってきたのだ。そろそろ新しいセッションを始めるのがおすすめなのだ",
}


class ZundaSpeaker(BaseHandler):
    """Handles Zunda voice notifications"""

    def __init__(self):
        self.enabled = zunda_config.enabled
        self.command_formatter = CommandFormatter()
        self.error_logger = get_error_logger()

    def handle_event(self, event: HookEvent) -> None:
        """Handle incoming hook event"""
        if not self.enabled:
            return

        # Test環境では音声をスキップ
        if self._is_test_environment():
            return

        # PreToolUseイベントの処理
        if event.hook_event_name in (HookEventName.PRE_TOOL_USE, "PreToolUse"):
            self._handle_pre_tool_use(event)
        elif event.hook_event_name in (HookEventName.NOTIFICATION, "Notification"):
            self._handle_notification(event)
        elif event.hook_event_name in (HookEventName.STOP, "Stop"):
            self._handle_stop(event)
        elif event.hook_event_name in (HookEventName.PRE_COMPACT, "PreCompact"):
            self._handle_pre_compact(event)

    def _handle_pre_tool_use(self, event: HookEvent) -> None:
        """Handle PreToolUse event"""
        if not event.tool_name or not event.tool_input:
            return

        voice_message = None

        if event.tool_name == "Task":
            description = event.tool_input.get("description", "")
            if description:
                voice_message = ZUNDAMON_MESSAGES["task_with_description"].format(
                    description=description
                )
            else:
                voice_message = ZUNDAMON_MESSAGES["task_execute"]

        elif event.tool_name == "Bash":
            cmd = event.tool_input.get("command", "")
            if cmd and not zunda_config.is_silent_command(cmd):
                # コマンドを読みやすい日本語に変換
                readable_cmd = self.command_formatter.format(cmd)
                voice_message = ZUNDAMON_MESSAGES["bash_command"].format(
                    command=readable_cmd
                )

                # Debug log for voice synthesis (only in non-test environment)
                if (
                    not self._is_test_environment()
                    and os.getenv("CCHH_ZUNDA_DEBUG", "").lower() == "true"
                ):
                    debug_log_path = os.path.join(os.getcwd(), "zunda_debug.log")
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(f"Original: {repr(cmd)}\n")
                        f.write(f"Readable: {repr(readable_cmd)}\n")
                        f.write(f"Voice message: {repr(voice_message)}\n")
                        f.write("---\n")

        elif event.tool_name == "TodoWrite":
            # TodoWriteは読み上げない（通知が多すぎるため）
            pass

        if voice_message:
            self._speak(voice_message)

    def _handle_notification(self, event: HookEvent) -> None:
        """Handle Notification event"""
        if not event.notification:
            return

        # Handle both string and dict notification formats
        if isinstance(event.notification, str):
            text = event.notification
        else:
            text = event.notification.get("text", "")

        # メッセージ変換マップで処理
        voice_message = ZUNDAMON_MESSAGES.get(text)

        if voice_message:
            # Permission messages use AMAAMA style
            if "permission" in text.lower():
                from .config import ZundaspeakStyle

                self._speak(voice_message, style=ZundaspeakStyle.AMAAMA.value)
            else:
                self._speak(voice_message)

    def _handle_stop(self, event: HookEvent) -> None:
        """Handle Stop event"""
        from .config import ZundaspeakStyle

        self._speak(ZUNDAMON_MESSAGES["session_end"], style=ZundaspeakStyle.SEXY.value)
    
    def _handle_pre_compact(self, event: HookEvent) -> None:
        """Handle PreCompact event"""
        _ = event  # Unused
        self._speak(ZUNDAMON_MESSAGES["pre_compact"])

    def _speak(self, message: str, style: str | None = None) -> None:
        """Send voice notification via zundaspeak"""
        if not message:
            return

        style = style or zunda_config.default_style.value

        try:
            # zundaspeak コマンドを実行
            subprocess.run(
                ["zundaspeak", "-s", style, message],
                capture_output=True,
                check=False,  # エラーでも例外を発生させない
            )
        except FileNotFoundError:
            # zundaspeak がインストールされていない場合
            if not hasattr(self, "_zundaspeak_warning_shown"):
                print(
                    "Warning: zundaspeak command not found. Voice notifications disabled."
                )
                self._zundaspeak_warning_shown = True
        except Exception as e:
            # その他のエラー
            self.error_logger.log_error(
                error_type="zundaspeak_error",
                error_message=str(e),
                context={
                    "message": message,
                    "style": style,
                },
                exception=e,
            )

    def _is_test_environment(self) -> bool:
        """Check if running in test environment"""
        return os.environ.get("CCHH_TEST_ENVIRONMENT", "").lower() in ("1", "true", "yes")
