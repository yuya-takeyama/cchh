"""Core type definitions for Claude Code Hooks"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HookEventName(Enum):
    """Enumeration of available hook event names"""

    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    NOTIFICATION = "Notification"
    STOP = "Stop"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_COMPACT = "PreCompact"


@dataclass
class HookEvent:
    """Represents a Claude Code hook event"""

    hook_event_name: str | HookEventName
    session_id: str
    cwd: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_response: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    prompt: str | None = None
    notification: str | None = None
    output: str | None = None
    raw_data: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HookEvent":
        """Create HookEvent from dictionary"""
        # Try to convert event name to enum if possible
        event_name = data.get("hook_event_name", "Unknown")
        try:
            # Try to find matching enum value
            for enum_member in HookEventName:
                if enum_member.value == event_name:
                    event_name = enum_member
                    break
        except Exception:
            # Keep as string if conversion fails
            pass

        return cls(
            hook_event_name=event_name,
            session_id=data.get("session_id", ""),
            cwd=data.get("cwd", ""),
            tool_name=data.get("tool_name"),
            tool_input=data.get("tool_input"),
            tool_response=data.get("tool_response"),
            result=data.get("result"),
            prompt=data.get("prompt"),
            notification=data.get("notification"),
            output=data.get("output"),
            raw_data=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output

        Claude Code expects a flat format for hook responses, not nested.
        We need to return the flattened data, not the raw nested structure.
        """
        # Build flat structure from fields
        # Handle both string and enum for hook_event_name
        event_name = self.hook_event_name
        if isinstance(event_name, HookEventName):
            event_name = event_name.value

        result: dict[str, Any] = {
            "hook_event_name": event_name,
            "session_id": self.session_id,
            "cwd": self.cwd,
        }

        # Add optional fields if present
        if self.tool_name:
            result["tool_name"] = self.tool_name
        if self.tool_input:
            result["tool_input"] = self.tool_input
        if self.tool_response:
            result["tool_response"] = self.tool_response
        if self.notification:
            result["notification"] = self.notification
        if self.output:
            result["output"] = self.output
        if self.result:
            result["result"] = self.result

        # Preserve any additional fields from raw_data that aren't standard
        if self.raw_data:
            # Get the actual data (handle nested format)
            source_data = self.raw_data
            if "data" in self.raw_data and isinstance(self.raw_data["data"], dict):
                source_data = self.raw_data["data"]

            # Add any non-standard fields
            standard_fields = {
                "hook_event_name",
                "session_id",
                "cwd",
                "tool_name",
                "tool_input",
                "tool_response",
                "result",
                "prompt",
                "notification",
                "output",
                "data",
            }
            for key, value in source_data.items():
                if key not in standard_fields and key not in result:
                    result[key] = value

        return result
