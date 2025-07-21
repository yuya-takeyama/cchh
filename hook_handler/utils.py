"""Utility functions for hook handler"""

import shlex
import sys
from pathlib import Path
from typing import Any

# Global converter instance
_converter = None


def is_test_environment() -> bool:
    """テスト環境かどうかを判定"""
    import os

    # unittest実行中の検出
    if "unittest" in sys.modules:
        return True

    # pytest実行中の検出
    if "pytest" in sys.modules:
        return True

    # 環境変数による明示的な指定
    if os.environ.get("TEST_ENVIRONMENT", "").lower() in ("1", "true", "yes"):
        return True

    return False


def get_session_id(hook_data: dict[str, Any] | None = None) -> str:
    """セッションIDを取得"""
    import os

    # hookデータから取得を試行
    if hook_data and "session_id" in hook_data:
        return hook_data["session_id"]

    # 環境変数から取得を試行
    session_id = os.environ.get("CLAUDE_SESSION_ID")
    if session_id:
        return session_id

    # デフォルトセッションID（フォールバック）
    return "default"


def truncate_command(cmd: str | None) -> str:
    """Truncate long commands for display"""
    if not cmd:
        return cmd or ""

    try:
        # Try to parse with shlex
        parts = shlex.split(cmd)
    except ValueError:
        # If shlex fails, return just the first word
        return cmd.split()[0] if cmd.split() else cmd

    # If we have no parts, return original
    if not parts:
        return cmd

    truncated_parts = []

    # Always include the command itself
    command_name = parts[0]
    truncated_parts.append(command_name)

    # Special handling for git, gh, and pnpm commands
    if command_name in ["git", "gh", "pnpm"]:
        # Collect only the first non-option argument (subcommand)
        for arg in parts[1:]:
            if not arg.startswith("-"):
                truncated_parts.append(arg)
                break

    return " ".join(truncated_parts)


def format_cwd_display(cwd: str) -> str:
    """Format current working directory for display"""
    home_dir = str(Path.home())
    if cwd.startswith(home_dir):
        return "~" + cwd[len(home_dir) :]
    return cwd


def format_cwd_for_slack(cwd: str) -> str:
    """Format current working directory for Slack display

    If cwd starts with $HOME/src/github.com/, remove that part.
    If cwd starts with $HOME, remove that part completely.
    Otherwise, return the full path.
    """
    home_dir = str(Path.home())
    github_prefix = home_dir + "/src/github.com/"

    if cwd.startswith(github_prefix):
        # Remove $HOME/src/github.com/ prefix
        return cwd[len(github_prefix) :]
    elif cwd.startswith(home_dir + "/"):
        # Remove home directory and the following slash
        return cwd[len(home_dir) + 1 :]
    elif cwd == home_dir:
        # If cwd is exactly the home directory, return "~"
        return "~"
    return cwd


def extract_permission_tool_name(message: str) -> str:
    """Extract tool name from permission request message"""
    if "bash" in message.lower():
        return "Bash"
    elif "task" in message.lower():
        return "Task"
    elif "read" in message.lower():
        return "Read"
    elif "write" in message.lower():
        return "Write"
    elif "edit" in message.lower():
        return "Edit"
    else:
        # その他のツール名を抽出
        import re

        match = re.search(r"permission to use (\w+)", message.lower())
        if match:
            return match.group(1).title()
    return ""


def get_converter():
    """Get global command converter instance"""
    global _converter
    if _converter is None:
        from .command_converter import SimpleCommandConverter

        _converter = SimpleCommandConverter()
    return _converter


def convert_command_to_readable(command: str) -> str:
    """Convert command to readable format"""
    if not command:
        return command
    return get_converter().convert(command)
