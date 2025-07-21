"""Logging utilities for hook handler"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("hook_handler")


class HookLogger:
    """Log hook events to file"""

    def __init__(self, log_file: Path = settings.log_file):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, hook_type: str, data: dict[str, Any], session_id: str) -> None:
        """Log hook event to file"""
        # Skip logging in test environment
        if settings.test_environment:
            return

        log_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "hook_type": hook_type,
            "data": data,
            "session_id": session_id,
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")


class ErrorLogger:
    """Log errors to JSONL file"""

    def __init__(self, log_file: Path = settings.error_log_file):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Log error to JSONL file"""
        # Skip logging in test environment
        if settings.test_environment:
            return

        log_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
        }

        # Add exception details if available
        if exception:
            log_entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc(),
            }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                # Write as JSONL (one JSON object per line)
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # If we can't write to the error log, at least log to standard logger
            logger.error(f"Failed to write error log entry: {e}")


hook_logger = HookLogger()
error_logger = ErrorLogger()
