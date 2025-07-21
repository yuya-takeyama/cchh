"""Event logger configuration"""

import os
from pathlib import Path


class LoggerConfig:
    """Logger-specific configuration"""

    def __init__(self):
        # Logger settings
        self.enabled = self._get_bool_env("EVENT_LOGGING_ENABLED", True)

        # Log file locations
        self.log_dir = Path.home() / ".cchh" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.event_log_file = self.log_dir / "events.jsonl"
        self.max_log_size = (
            int(os.environ.get("LOG_MAX_SIZE_MB", "100")) * 1024 * 1024
        )  # MB to bytes
        self.log_rotation_count = int(os.environ.get("LOG_ROTATION_COUNT", "5"))

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.environ.get(key, str(default)).lower()
        return value in ("1", "true", "yes")


# Global instance
logger_config = LoggerConfig()
