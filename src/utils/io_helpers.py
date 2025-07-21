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
        data = json.loads(stream.read())
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON input: {e.msg}", e.doc, e.pos) from e

    # Validate required fields
    if "hook_event_name" not in data:
        raise ValueError("Missing required field: hook_event_name")

    # Set defaults for commonly missing fields
    if "session_id" not in data:
        data["session_id"] = "unknown"
    if "cwd" not in data:
        import os

        data["cwd"] = os.getcwd()

    return HookEvent.from_dict(data)


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
