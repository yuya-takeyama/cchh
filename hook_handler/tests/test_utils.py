"""Test cases for utility functions"""

import os
from unittest.mock import patch

from hook_handler.utils import (
    extract_permission_tool_name,
    format_cwd_display,
    format_cwd_for_slack,
    get_session_id,
    is_test_environment,
    truncate_command,
)


def test_unittest_detection():
    """Test unittest/pytest module detection"""
    # Since we're running tests, it should detect it
    assert is_test_environment() is True


@patch.dict(os.environ, {"TEST_ENVIRONMENT": "1"})
def test_env_var_true():
    """Test with TEST_ENVIRONMENT=1"""
    assert is_test_environment() is True


@patch.dict(os.environ, {"TEST_ENVIRONMENT": "true"})
def test_env_var_true_string():
    """Test with TEST_ENVIRONMENT=true"""
    assert is_test_environment() is True


@patch.dict(os.environ, {"TEST_ENVIRONMENT": "false"})
def test_env_var_false_with_unittest():
    """Test with TEST_ENVIRONMENT=false but pytest loaded"""
    # Should still be True because pytest is loaded
    assert is_test_environment() is True


def test_from_hook_data():
    """Test getting session ID from hook data"""
    hook_data = {"session_id": "test-session-123"}
    assert get_session_id(hook_data) == "test-session-123"


@patch.dict(os.environ, {"CLAUDE_SESSION_ID": "env-session-456"})
def test_from_env_var():
    """Test getting session ID from environment variable"""
    assert get_session_id() == "env-session-456"


def test_default_fallback():
    """Test default session ID fallback"""
    with patch.dict(os.environ, {}, clear=True):
        assert get_session_id() == "default"


@patch.dict(os.environ, {"CLAUDE_SESSION_ID": "env-session"})
def test_hook_data_priority():
    """Test hook data has priority over env var"""
    hook_data = {"session_id": "hook-session"}
    assert get_session_id(hook_data) == "hook-session"


def test_empty_command():
    """Test with empty command"""
    assert truncate_command("") == ""
    assert truncate_command(None) == ""


def test_simple_command():
    """Test with simple commands"""
    assert truncate_command("ls") == "ls"
    assert truncate_command("pwd") == "pwd"
    assert truncate_command("echo hello") == "echo"


def test_git_commands():
    """Test git command truncation"""
    assert truncate_command("git status") == "git status"
    assert truncate_command("git commit") == "git commit"
    assert truncate_command("git commit -m 'message'") == "git commit"
    assert truncate_command("git add file.txt") == "git add"
    assert truncate_command("git checkout -b feature/new") == "git checkout"
    assert truncate_command("git push origin main") == "git push"


def test_pnpm_commands():
    """Test pnpm command truncation"""
    assert truncate_command("pnpm install") == "pnpm install"
    assert truncate_command("pnpm install @types/node") == "pnpm install"
    assert truncate_command("pnpm run dev") == "pnpm run"
    assert truncate_command("pnpm run dev --force") == "pnpm run"


def test_gh_commands():
    """Test gh command truncation"""
    assert truncate_command("gh pr create") == "gh pr"
    assert truncate_command("gh pr create --title 'Title'") == "gh pr"
    assert truncate_command("gh issue list") == "gh issue"


def test_complex_commands():
    """Test complex commands with multiple options"""
    assert (
        truncate_command("git commit -m 'Long message' --amend --no-edit")
        == "git commit"
    )
    assert (
        truncate_command("pnpm install --save-dev @types/node prettier eslint")
        == "pnpm install"
    )


def test_shlex_failure():
    """Test when shlex parsing fails"""
    # Command with unclosed quote
    result = truncate_command("echo 'unclosed")
    assert result == "echo"


def test_home_dir_replacement():
    """Test home directory is replaced with ~"""
    from pathlib import Path

    home = str(Path.home())

    # Test exact home directory
    assert format_cwd_display(home) == "~"

    # Test subdirectory
    assert format_cwd_display(f"{home}/projects") == "~/projects"
    assert format_cwd_display(f"{home}/Documents/work") == "~/Documents/work"


def test_non_home_dir():
    """Test directories outside home are unchanged"""
    assert format_cwd_display("/tmp") == "/tmp"
    assert format_cwd_display("/usr/local/bin") == "/usr/local/bin"


def test_home_dir_removal():
    """Test home directory is removed from path"""
    from pathlib import Path

    home = str(Path.home())

    # Test exact home directory
    assert format_cwd_for_slack(home) == "~"

    # Test subdirectory
    assert format_cwd_for_slack(f"{home}/projects") == "projects"
    assert format_cwd_for_slack(f"{home}/Documents/work") == "Documents/work"
    assert format_cwd_for_slack(f"{home}/.claude/scripts") == ".claude/scripts"


def test_non_home_dir_slack():
    """Test directories outside home are unchanged"""
    assert format_cwd_for_slack("/tmp") == "/tmp"
    assert format_cwd_for_slack("/usr/local/bin") == "/usr/local/bin"
    assert format_cwd_for_slack("/var/log") == "/var/log"


def test_github_dir_removal():
    """Test $HOME/src/github.com/ prefix is removed"""
    from pathlib import Path

    home = str(Path.home())
    github_prefix = f"{home}/src/github.com/"

    # Test GitHub repository paths
    assert (
        format_cwd_for_slack(f"{github_prefix}yuya-takeyama/dok") == "yuya-takeyama/dok"
    )
    assert (
        format_cwd_for_slack(f"{github_prefix}anthropics/claude-code")
        == "anthropics/claude-code"
    )
    assert (
        format_cwd_for_slack(f"{github_prefix}owner/repo/subdir") == "owner/repo/subdir"
    )

    # Test exact github prefix (unlikely but should handle gracefully)
    assert format_cwd_for_slack(github_prefix.rstrip("/")) == "src/github.com"

    # Test non-GitHub paths under home are still handled correctly
    assert format_cwd_for_slack(f"{home}/src/projects") == "src/projects"
    assert format_cwd_for_slack(f"{home}/Documents") == "Documents"


def test_standard_tools():
    """Test extraction of standard tool names"""
    test_cases = [
        ("Claude needs your permission to use Bash", "Bash"),
        ("Claude needs your permission to use Task", "Task"),
        ("Claude needs your permission to use Read", "Read"),
        ("Claude needs your permission to use Write", "Write"),
        ("Claude needs your permission to use Edit", "Edit"),
    ]

    for message, expected in test_cases:
        assert extract_permission_tool_name(message) == expected


def test_case_insensitive():
    """Test case insensitive matching"""
    assert (
        extract_permission_tool_name("claude needs your permission to use bash")
        == "Bash"
    )


def test_regex_extraction():
    """Test regex extraction for other tools"""
    assert (
        extract_permission_tool_name("Claude needs your permission to use WebSearch")
        == "Websearch"  # Capitalized version
    )


def test_no_match():
    """Test when no tool name is found"""
    assert extract_permission_tool_name("Some other message") == ""
