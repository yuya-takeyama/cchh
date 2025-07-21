"""Configuration settings for hook handler"""

import os
from enum import Enum
from pathlib import Path


class NotificationLevel(Enum):
    """通知レベル"""

    CHANNEL = "channel"
    THREAD = "thread"


class ZundaspeakStyle(Enum):
    """Zundaspeakの読み上げスタイル"""

    NORMAL = "0"  # ノーマル
    AMAAMA = "1"  # あまあま
    TSUNTSUN = "2"  # ツンツン
    SEXY = "3"  # セクシー
    SASAYAKI = "4"  # ささやき
    HISOHISO = "5"  # ヒソヒソ
    HEROHERO = "6"  # ヘロヘロ
    NAMIDAME = "7"  # なみだめ


class Settings:
    """Application settings"""

    def __init__(self):
        self.home_dir = Path.home()
        self.claude_dir = self.home_dir / ".claude"
        self.thread_dir = self.claude_dir / "slack_thread_ts"
        self.log_file = self.claude_dir / "hooks.log"
        self.error_log_file = self.claude_dir / "hook_handler_errors.log"

        # Slack settings
        self.slack_enabled = self._get_bool_env("SLACK_ENABLED", True)
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_channel_id = os.environ.get("SLACK_CHANNEL_ID")

        # Test environment detection - removed from __init__ to make it dynamic

        # Ensure directories exist
        self.thread_dir.mkdir(parents=True, exist_ok=True)
        self.claude_dir.mkdir(parents=True, exist_ok=True)

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.environ.get(key, str(default)).lower()
        return value in ("1", "true", "yes")

    @property
    def slack_configured(self) -> bool:
        """Check if Slack is properly configured"""
        return bool(self.slack_bot_token and self.slack_channel_id)

    @property
    def test_environment(self) -> bool:
        """Check if running in test environment (dynamic evaluation)"""
        return os.environ.get("TEST_ENVIRONMENT", "").lower() in (
            "1",
            "true",
            "yes",
        )


settings = Settings()
