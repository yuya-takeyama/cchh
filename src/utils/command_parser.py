"""Command parsing utilities"""

import shlex
from typing import Any


def parse_bash_command(command: str) -> dict[str, Any]:
    """Parse bash command into structured format

    Args:
        command: Raw bash command string

    Returns:
        Dictionary with command components:
        - command: The base command name
        - args: List of arguments
        - options: Dictionary of options (flags)
        - raw: Original command string
    """
    result: dict[str, Any] = {
        "command": "",
        "args": [],
        "options": {},
        "raw": command,
    }

    # Handle empty command
    if not command or not command.strip():
        return result

    try:
        # Use shlex to properly parse the command
        parts = shlex.split(command)
        if not parts:
            return result

        # First part is the command
        result["command"] = parts[0]

        # Parse remaining parts
        i = 1
        while i < len(parts):
            part = parts[i]

            if part.startswith("-"):
                # This is an option/flag
                if i + 1 < len(parts) and not parts[i + 1].startswith("-"):
                    # Option with value
                    result["options"][part] = parts[i + 1]
                    i += 2
                else:
                    # Boolean flag
                    result["options"][part] = True
                    i += 1
            else:
                # Regular argument
                result["args"].append(part)
                i += 1

    except (ValueError, Exception):
        # If shlex fails, do basic splitting
        parts = command.split()
        if parts:
            result["command"] = parts[0]
            result["args"] = parts[1:] if len(parts) > 1 else []

    return result


def extract_command_name(command: str) -> str:
    """Extract just the command name from a bash command

    Args:
        command: Full bash command

    Returns:
        Command name only
    """
    parsed = parse_bash_command(command)
    return parsed["command"]


def is_pipeline_command(command: str) -> bool:
    """Check if command contains pipes or redirections

    Args:
        command: Bash command to check

    Returns:
        True if command contains pipes or redirections
    """
    return any(op in command for op in ["|", ">", "<", ">>", "<<"])


def split_pipeline(command: str) -> list[str]:
    """Split pipeline command into individual commands

    Args:
        command: Pipeline command

    Returns:
        List of individual commands
    """
    # Simple split by pipe - doesn't handle quoted pipes
    if "|" in command:
        return [cmd.strip() for cmd in command.split("|")]
    return [command]


def get_command_category(command: str) -> str:
    """Categorize command for notification purposes

    Args:
        command: Command to categorize

    Returns:
        Category name: "git", "npm", "docker", "file", "system", "other"
    """
    cmd_name = extract_command_name(command).lower()

    # Git commands
    if cmd_name in ["git", "gh"]:
        return "git"

    # Package managers
    if cmd_name in ["npm", "yarn", "pnpm", "pip", "poetry", "uv"]:
        return "npm"

    # Container/orchestration
    if cmd_name in ["docker", "docker-compose", "kubectl", "helm"]:
        return "docker"

    # File operations
    if cmd_name in ["cp", "mv", "rm", "mkdir", "touch", "chmod", "chown"]:
        return "file"

    # System commands
    if cmd_name in ["sudo", "systemctl", "service", "ps", "kill"]:
        return "system"

    return "other"
