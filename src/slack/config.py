"""Slack notification configuration"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class NotificationLevel(Enum):
    """通知レベル"""

    CHANNEL = "channel"
    THREAD = "thread"


@dataclass
class RuntimeConfig:
    """実行時設定（環境変数から独立）"""

    is_test_environment: bool
    notifications_enabled: bool
    show_session_start: bool
    notify_on_tool_use: bool
    notify_on_stop: bool
    bot_token: str | None
    channel_id: str | None
    command_max_length: int
    session_id_length: int
    thread_dir: Path

    @classmethod
    def from_environment(cls) -> "RuntimeConfig":
        """環境変数から設定を読み込む（環境依存部分を集約）"""

        def _get_bool_env(key: str, default: bool) -> bool:
            value = os.environ.get(key, str(default)).lower()
            return value in ("1", "true", "yes")

        thread_dir = Path.home() / ".cchh" / "slack_threads"

        return cls(
            is_test_environment=os.getenv("CCHH_TEST_ENVIRONMENT", "").lower()
            == "true",
            notifications_enabled=_get_bool_env(
                "CCHH_SLACK_NOTIFICATIONS_ENABLED", True
            ),
            show_session_start=_get_bool_env("CCHH_SLACK_SHOW_SESSION_START", True),
            notify_on_tool_use=_get_bool_env("CCHH_SLACK_NOTIFY_ON_TOOL_USE", True),
            notify_on_stop=_get_bool_env("CCHH_SLACK_NOTIFY_ON_STOP", True),
            bot_token=os.environ.get("CCHH_SLACK_BOT_TOKEN"),
            channel_id=os.environ.get("CCHH_SLACK_CHANNEL_ID"),
            command_max_length=int(
                os.environ.get("CCHH_SLACK_COMMAND_MAX_LENGTH", "200")
            ),
            session_id_length=int(os.environ.get("CCHH_SLACK_SESSION_ID_LENGTH", "8")),
            thread_dir=thread_dir,
        )

    @property
    def is_configured(self) -> bool:
        """Check if Slack is properly configured"""
        return self.bot_token is not None and self.channel_id is not None


class SlackConfig:
    """Slack-specific configuration"""

    def __init__(self):
        # Slack settings
        self.enabled = self._get_bool_env("CCHH_SLACK_NOTIFICATIONS_ENABLED", True)
        self.bot_token = os.environ.get("CCHH_SLACK_BOT_TOKEN")
        self.channel_id = os.environ.get("CCHH_SLACK_CHANNEL_ID")

        # Slack feature toggles
        self.show_session_start = self._get_bool_env(
            "CCHH_SLACK_SHOW_SESSION_START", True
        )
        self.notify_on_tool_use = self._get_bool_env(
            "CCHH_SLACK_NOTIFY_ON_TOOL_USE", True
        )
        self.notify_on_stop = self._get_bool_env("CCHH_SLACK_NOTIFY_ON_STOP", True)
        self.command_max_length = int(
            os.environ.get("CCHH_SLACK_COMMAND_MAX_LENGTH", "200")
        )

        # Thread management directory
        self.thread_dir = Path.home() / ".cchh" / "slack_threads"
        self.thread_dir.mkdir(parents=True, exist_ok=True)

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.environ.get(key, str(default)).lower()
        return value in ("1", "true", "yes")

    @property
    def is_configured(self) -> bool:
        """Check if Slack is properly configured"""
        return self.bot_token is not None and self.channel_id is not None


# Global instance
slack_config: SlackConfig = SlackConfig()
