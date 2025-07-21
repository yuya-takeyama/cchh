"""Core type definitions for Claude Code Hooks"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional


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
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None
    notification: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookEvent":
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

    def to_dict(self) -> Dict[str, Any]:
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
