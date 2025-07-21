"""Slack notification configuration"""

import os
from enum import Enum
from pathlib import Path


class NotificationLevel(Enum):
    """通知レベル"""

    CHANNEL = "channel"
    THREAD = "thread"


class SlackConfig:
    """Slack-specific configuration"""

    def __init__(self):
        # Slack settings
        self.enabled = self._get_bool_env("SLACK_NOTIFICATIONS_ENABLED", True)
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.channel_id = os.environ.get("SLACK_CHANNEL_ID")

        # Slack feature toggles
        self.show_session_start = self._get_bool_env("SLACK_SHOW_SESSION_START", True)
        self.notify_on_tool_use = self._get_bool_env("SLACK_NOTIFY_ON_TOOL_USE", True)
        self.notify_on_stop = self._get_bool_env("SLACK_NOTIFY_ON_STOP", True)
        self.command_max_length = int(os.environ.get("SLACK_COMMAND_MAX_LENGTH", "200"))

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
        return bool(self.bot_token and self.channel_id)


# Global instance
slack_config = SlackConfig()
