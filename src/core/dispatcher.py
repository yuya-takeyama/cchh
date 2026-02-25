"""Event dispatcher for Claude Code Hooks"""

import os

from .base import HookHandler
from .types import HookEvent


class EventDispatcher:
    """Dispatches hook events to appropriate handlers"""

    def __init__(self):
        self.zunda: HookHandler | None = self._init_zunda()
        self.logger: HookHandler | None = self._init_logger()

    def _init_zunda(self) -> HookHandler | None:
        """Initialize Zunda speaker if enabled"""
        if os.getenv("CCHH_ZUNDA_SPEAKER_ENABLED", "true").lower() == "true":
            try:
                from ..zunda.speaker import ZundaSpeaker

                return ZundaSpeaker()
            except ImportError:
                print("Warning: Zunda module not found")
                return None
        return None

    def _init_logger(self) -> HookHandler | None:
        """Initialize event logger if enabled"""
        if os.getenv("CCHH_EVENT_LOGGING_ENABLED", "true").lower() == "true":
            try:
                from ..logger.event_logger import EventLogger

                return EventLogger()
            except ImportError:
                print("Warning: Logger module not found")
                return None
        return None

    def dispatch(self, event: HookEvent) -> None:
        """Dispatch event to all enabled handlers"""
        # 各機能に並列でイベントを渡す
        if self.zunda:
            try:
                self.zunda.handle_event(event)
            except Exception as e:
                print(f"Zunda handler error: {e}")

        if self.logger:
            try:
                self.logger.handle_event(event)
            except Exception as e:
                print(f"Logger handler error: {e}")
