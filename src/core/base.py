"""Base handler definitions for Claude Code Hooks"""

from abc import ABC, abstractmethod
from typing import Protocol

from .types import HookEvent


class HookHandler(Protocol):
    """Protocol defining the interface for all hook handlers"""

    def handle_event(self, event: HookEvent) -> None:
        """Handle a hook event

        Args:
            event: The hook event to process
        """
        ...


class BaseHandler(ABC):
    """Abstract base class for hook handlers with common functionality"""

    @abstractmethod
    def handle_event(self, event: HookEvent) -> None:
        """Handle a hook event

        Args:
            event: The hook event to process
        """
        pass
