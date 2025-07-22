"""Event logger for Claude Code Hooks"""

import json
from datetime import datetime
from pathlib import Path

from ..core.base import BaseHandler
from ..core.types import HookEvent
from ..utils.config import is_test_environment
from ..utils.logger import get_debug_logger
from .config import logger_config


class EventLogger(BaseHandler):
    """Logs all hook events to JSONL file"""

    def __init__(self, log_file: Path | None = None):
        self.enabled = logger_config.enabled
        self.log_file = log_file or logger_config.event_log_file
        self.debug_logger = get_debug_logger()

        # Ensure log directory exists
        if self.enabled:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def handle_event(self, event: HookEvent) -> None:
        """Handle incoming hook event"""
        if not self.enabled or is_test_environment():
            return

        # Log all events
        self._log_event(event)

        # Check if rotation is needed
        self._check_rotation()

    def _log_event(self, event: HookEvent) -> None:
        """Log event to file"""
        # Create log entry with time and raw_input
        log_entry = {
            "time": datetime.now().isoformat() + "Z",
            "raw_input": event.to_dict()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.debug_logger.error(f"Failed to write log entry: {e}")

    def _check_rotation(self) -> None:
        """Check if log rotation is needed"""
        try:
            if not self.log_file.exists():
                return

            file_size = self.log_file.stat().st_size
            if file_size > logger_config.max_log_size:
                self._rotate_logs()
        except Exception as e:
            self.debug_logger.error(f"Error checking log rotation: {e}")

    def _rotate_logs(self) -> None:
        """Rotate log files"""
        try:
            # Remove oldest log if at max count
            oldest = (
                self.log_file.parent
                / f"{self.log_file.stem}.{logger_config.log_rotation_count}"
            )
            if oldest.exists():
                oldest.unlink()

            # Rotate existing logs
            for i in range(logger_config.log_rotation_count - 1, 0, -1):
                current = self.log_file.parent / f"{self.log_file.stem}.{i}"
                next_num = self.log_file.parent / f"{self.log_file.stem}.{i + 1}"
                if current.exists():
                    current.rename(next_num)

            # Rotate current log
            self.log_file.rename(self.log_file.parent / f"{self.log_file.stem}.1")

            self.debug_logger.info("Log files rotated successfully")
        except Exception as e:
            self.debug_logger.error(f"Error rotating logs: {e}")

    def get_recent_events(
        self, count: int = 100, session_id: str | None = None
    ) -> list:
        """Get recent events from log

        Args:
            count: Number of events to retrieve
            session_id: Filter by session ID if provided

        Returns:
            List of recent events
        """
        if not self.log_file.exists():
            return []

        events = []
        try:
            with open(self.log_file, encoding="utf-8") as f:
                # Read from end of file for efficiency
                lines = f.readlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                        if session_id and event.get("session_id") != session_id:
                            continue

                        events.append(event)
                        if len(events) >= count:
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.debug_logger.error(f"Error reading events: {e}")

        return list(reversed(events))
