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
    result: dict[str, Any] | None = None
    prompt: str | None = None
    notification: dict[str, Any] | None = None
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
            result=data.get("result"),
            prompt=data.get("prompt"),
            notification=data.get("notification"),
            output=data.get("output"),
            raw_data=data,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output"""
        if self.raw_data:
            return self.raw_data

        # Convert enum to string if necessary
        event_name = self.hook_event_name
        if isinstance(event_name, HookEventName):
            event_name = event_name.value

        data: dict[str, Any] = {
            "hook_event_name": event_name,
            "session_id": self.session_id,
            "cwd": self.cwd,
        }

        if self.tool_name is not None:
            data["tool_name"] = self.tool_name
        if self.tool_input is not None:
            data["tool_input"] = self.tool_input
        if self.result is not None:
            data["result"] = self.result
        if self.prompt is not None:
            data["prompt"] = self.prompt
        if self.notification is not None:
            data["notification"] = self.notification
        if self.output is not None:
            data["output"] = self.output

        return data
