"""Logging utilities for error tracking and debugging"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ErrorLogger:
    """Handles error logging to file"""

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path.home() / ".cchh" / "errors.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        """Log error to file with context"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
        }

        if exception:
            error_entry["traceback"] = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_entry) + "\n")
        except Exception as e:
            # If we can't write to file, at least print to stderr
            print(f"Failed to write to error log: {e}", file=sys.stderr)


class DebugLogger:
    """Simple debug logger for development"""

    def __init__(self, name: str = "cchh"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Only add handler if not already added
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, **kwargs)


# Global instances
_error_logger = None
_debug_logger = None


def get_error_logger() -> ErrorLogger:
    """Get global error logger instance"""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger


def get_debug_logger() -> DebugLogger:
    """Get global debug logger instance"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger
