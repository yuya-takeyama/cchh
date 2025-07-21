"""Core type definitions for Claude Code Hooks"""

from dataclasses import dataclass
from typing import Any, Literal

HookEventName = Literal[
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "UserPromptSubmit",
]


@dataclass
class HookEvent:
    """Represents a Claude Code hook event"""

    hook_event_name: HookEventName
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
        return cls(
            hook_event_name=data.get("hook_event_name", "Unknown"),
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

        result = {
            "hook_event_name": self.hook_event_name,
            "session_id": self.session_id,
            "cwd": self.cwd,
        }

        if self.tool_name is not None:
            result["tool_name"] = self.tool_name
        if self.tool_input is not None:
            result["tool_input"] = self.tool_input
        if self.result is not None:
            result["result"] = self.result
        if self.prompt is not None:
            result["prompt"] = self.prompt
        if self.notification is not None:
            result["notification"] = self.notification
        if self.output is not None:
            result["output"] = self.output

        return result
