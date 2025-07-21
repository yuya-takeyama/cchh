"""Notification handlers (Slack and Zundaspeak)"""

import json
import subprocess
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from .config import NotificationLevel, settings
from .logger import error_logger
from .utils import is_test_environment


class NotifierBase(ABC):
    """Base class for notifiers"""

    @abstractmethod
    def notify(self, message: str, **kwargs) -> Any:
        """Send notification"""
        pass


class SlackNotifier(NotifierBase):
    """Slack notification handler"""

    def __init__(self):
        self.api_url = "https://slack.com/api/chat.postMessage"

    def should_send(self) -> bool:
        """Slack通知を送信すべきかどうかを判定"""
        # テスト環境では送信しない
        if is_test_environment():
            return False

        # SLACK_ENABLEDでOFFになっている場合は送信しない
        if not settings.slack_enabled:
            return False

        # 必要な環境変数が設定されているかチェック
        return settings.slack_configured

    def notify(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.THREAD,
        session_manager=None,
        broadcast: bool = False,
        cwd: str | None = None,
        **kwargs,
    ) -> str | None:
        """Slackにメッセージを投稿"""
        if not self.should_send():
            return None

        # cwdがない場合は現在のディレクトリを取得
        if cwd is None:
            import os

            cwd = os.getcwd()

        # スレッド管理
        thread_state = session_manager.load_state() if session_manager else None
        is_new_thread = not thread_state or not thread_state.get("thread_ts")

        # 新規スレッドまたはbroadcast時のメッセージ処理
        # :clapper:の行は変更しない（cwdが含まれる）

        data = {
            "channel": settings.slack_channel_id,
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
            "Authorization": f"Bearer {settings.slack_bot_token}",
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
                    if message_ts and is_new_thread and session_manager:
                        session_manager.save_state(message_ts)

                    return message_ts
                else:
                    # エラーログ出力（ただし詳細は出さない）
                    import sys

                    print(
                        f"Slack notification failed: {result.get('error', 'Unknown error')}",
                        file=sys.stderr,
                    )

                    # Log to error file
                    error_logger.log_error(
                        error_type="slack_api_error",
                        error_message=f"Slack API error: {result.get('error', 'Unknown error')}",
                        context={
                            "channel": settings.slack_channel_id,
                            "message_preview": message[:100] if message else "",
                            "level": level.value,
                            "thread_ts": data.get("thread_ts"),
                            "response": result,
                        },
                    )
                    return None

        except Exception as e:
            # 通知失敗してもメイン処理は止めない
            import sys

            print(f"Slack notification error: {e}", file=sys.stderr)

            # Log to error file
            error_logger.log_error(
                error_type="slack_notification_error",
                error_message=str(e),
                context={
                    "channel": settings.slack_channel_id,
                    "message_preview": message[:100] if message else "",
                    "level": level.value,
                    "cwd": cwd,
                },
                exception=e,
            )
            return None


class ZundaspeakNotifier(NotifierBase):
    """Zundaspeak voice notification handler"""

    def notify(self, message: str, style: str = "0", **kwargs) -> None:
        """Send voice notification via zundaspeak"""
        try:
            subprocess.run(["zundaspeak", "-s", style, message], capture_output=True)
        except Exception as e:
            # Log to error file but don't interrupt the flow
            error_logger.log_error(
                error_type="zundaspeak_error",
                error_message=str(e),
                context={
                    "message": message,
                    "style": style,
                },
                exception=e,
            )


# Singleton instances
slack_notifier = SlackNotifier()
zundaspeak_notifier = ZundaspeakNotifier()
