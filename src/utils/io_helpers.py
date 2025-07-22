"""I/O helper functions"""

import json
import sys
from typing import Any, TextIO

from ..core.types import HookEvent


def load_hook_event(stream: TextIO | None = None) -> HookEvent:
    """Load hook event from JSON input stream

    Args:
        stream: Input stream (defaults to sys.stdin)

    Returns:
        HookEvent object

    Raises:
        json.JSONDecodeError: If input is not valid JSON
        ValueError: If required fields are missing
    """
    if stream is None:
        stream = sys.stdin

    try:
        raw_data = json.loads(stream.read())
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON input: {e.msg}", e.doc, e.pos) from e

    # Handle nested Claude Code event structure
    data = _normalize_hook_event_data(raw_data)

    # Validate required fields
    if "hook_event_name" not in data:
        raise ValueError("Missing required field: hook_event_name")

    # Set defaults for commonly missing fields
    if "session_id" not in data:
        data["session_id"] = "unknown"
    if "cwd" not in data:
        import os

        data["cwd"] = os.getcwd()

    # Create HookEvent with normalized data but preserve original raw_data
    event = HookEvent.from_dict(data)
    # Override raw_data with the original nested structure
    event.raw_data = raw_data
    return event


def _normalize_hook_event_data(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize Claude Code event data structure

    Handles both the actual nested format from Claude Code and the flat format
    expected by tests and internal code.

    Args:
        raw_data: Raw event data from Claude Code

    Returns:
        Normalized flat event data
    """
    # If already in flat format (tests, legacy), handle message->notification mapping
    if "hook_event_name" in raw_data and "data" not in raw_data:
        data = raw_data.copy()
        
        # Special handling for Notification events in flat format
        if (
            data.get("hook_event_name") == "Notification"
            and "message" in data
            and "notification" not in data
        ):
            # Map message to notification field
            data["notification"] = data["message"]
        
        return data

    # Handle nested Claude Code format
    if "data" in raw_data:
        # Start with the nested data
        data = raw_data["data"].copy()

        # Copy top-level fields that aren't in nested data
        for key, value in raw_data.items():
            if key != "data" and key not in data:
                data[key] = value

        # Special handling for Notification events
        if (
            data.get("hook_event_name") == "Notification"
            and "message" in data
            and "notification" not in data
        ):
            # Map data.message to notification field
            data["notification"] = data["message"]

        return data

    # Fallback: return original data
    return raw_data.copy()


def write_hook_event(event: HookEvent, stream: TextIO | None = None) -> None:
    """Write hook event to output stream

    Args:
        event: HookEvent to write
        stream: Output stream (defaults to sys.stdout)
    """
    if stream is None:
        stream = sys.stdout

    json.dump(event.to_dict(), stream)
    stream.flush()


def load_json_file(file_path: str) -> dict[str, Any]:
    """Load JSON from file

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: dict[str, Any], file_path: str, indent: int = 2) -> None:
    """Save data as JSON to file

    Args:
        data: Data to save
        file_path: Path to save to
        indent: JSON indentation level
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def append_jsonl(data: dict[str, Any], file_path: str) -> None:
    """Append data as JSON line to file

    Args:
        data: Data to append
        file_path: Path to JSONL file
    """
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
