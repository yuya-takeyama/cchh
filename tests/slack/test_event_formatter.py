"""Test cases for EventFormatter"""

import pytest

from src.slack.config import NotificationLevel
from src.slack.event_formatter import EventFormatter


class TestEventFormatter:
    """Test cases for EventFormatter"""

    @pytest.fixture
    def formatter(self):
        """Create EventFormatter instance"""
        return EventFormatter()

    def test_format_command_single_line(self, formatter):
        """Test single line command formatting"""
        # Critical command (git push)
        command = "git push origin main"
        message, level = formatter.format_command(command)
        assert message == "🚨 コマンド実行: `git push origin main`"
        assert level == NotificationLevel.CHANNEL

        # Critical command
        command = "git commit -m 'Fix bug'"
        message, level = formatter.format_command(command)
        assert message == "🚨 コマンド実行: `git commit -m 'Fix bug'`"
        assert level == NotificationLevel.CHANNEL

        # Other command (not critical or important)
        command = "ls -la"
        message, level = formatter.format_command(command)
        assert message == "💻 コマンド実行: `ls -la`"
        assert level == NotificationLevel.THREAD

        # uv command
        command = "uv run task test"
        message, level = formatter.format_command(command)
        assert message == "💻 コマンド実行: `uv run task test`"
        assert level == NotificationLevel.THREAD

    def test_format_command_multi_line(self, formatter):
        """Test multi-line command formatting with code block"""
        # Multi-line git commit
        command = '''git commit -m "$(cat <<'EOF'
refactor: simplify CommandFormatter to configuration-based approach

- Refactor CommandFormatter to use two simple dictionaries
  - words: pronunciation mappings (now only npm, pnpm, tsx)
  - parts_limit: how many parts to read for each command
- Remove complex if-elif chains and special formatting
- Remove unnecessary word translations (kept only npm, pnpm, tsx)
- Add comprehensive table-driven tests for CommandFormatter
- Update existing tests to match new behavior
- Make the formatter a pure function for easier testing

This approach is more maintainable and easier to extend when needed.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"'''

        message, level = formatter.format_command(command)
        assert message.startswith("🚨 コマンド実行\n```\n$ ")
        assert "refactor: simplify CommandFormatter" in message
        assert message.endswith("\n```")
        assert level == NotificationLevel.CHANNEL

    def test_format_command_multi_line_important(self, formatter):
        """Test multi-line important (non-critical) command"""
        command = '''npm install --save-dev "$(cat <<'EOF'
@types/node
@types/react
@types/react-dom
EOF
)"'''

        message, level = formatter.format_command(command)
        assert message.startswith("⚡ コマンド実行\n```\n$ ")
        assert "@types/node" in message
        assert "```" in message
        assert level == NotificationLevel.THREAD

    def test_format_command_with_backticks(self, formatter):
        """Test command containing backticks gets escaped properly"""
        command = '''git commit -m "$(cat <<'EOF'
feat: add code blocks using ```

- Use format: emoji + "コマンド実行\n```\n$ command\n```" for multi-line
- This adds ``` delimiters for code blocks
EOF
)"'''

        message, level = formatter.format_command(command)
        assert message.startswith("🚨 コマンド実行\n```\n$ ")
        # Check that backticks are escaped
        assert "\\`\\`\\`" in message
        # Check specific escaped content
        assert "feat: add code blocks using \\`\\`\\`" in message
        assert "- This adds \\`\\`\\` delimiters for code blocks" in message
        # Ensure the message still ends with code block
        assert message.endswith("\n```")
        assert level == NotificationLevel.CHANNEL

    def test_format_command_multi_line_other(self, formatter):
        """Test multi-line command formatting for non-important commands"""
        command = '''uv run python -c "
import sys
print('Python version:', sys.version)
print('Hello from multi-line!')
"'''

        message, level = formatter.format_command(command)
        assert message.startswith("💻 コマンド実行\n```\n$ ")
        assert "Python version:" in message
        assert "Hello from multi-line!" in message
        assert message.endswith("\n```")
        assert level == NotificationLevel.THREAD

    def test_format_session_start(self, formatter):
        """Test session start formatting"""
        # Test with absolute path (not home directory)
        message = formatter.format_session_start("test-session-123", "/tmp/project")
        assert message == ":clapper: `test-ses` `/tmp/project`"

        # Test with home directory path
        import os

        home_path = os.path.expanduser("~/project")
        message = formatter.format_session_start("test-session-123", home_path)
        assert "`test-ses`" in message
        assert "`~/project`" in message

        # Test with long session ID
        long_session_id = "32334be6-ebad-42a6-b54e-ce108a16ee46"
        message = formatter.format_session_start(long_session_id, "/tmp/project")
        assert "`32334be6`" in message

        # Test with github.com repository path
        home = os.path.expanduser("~")
        github_path = os.path.join(home, "src", "github.com", "yuya-takeyama", "cchh")
        message = formatter.format_session_start(long_session_id, github_path)
        assert "`32334be6`" in message
        assert "`yuya-takeyama/cchh`" in message

        # Test with other home directory path
        home_other_path = os.path.expanduser("~/.claude/scripts")
        message = formatter.format_session_start("test-session", home_other_path)
        assert "`test-ses`" in message
        assert "`~/.claude/scripts`" in message

    def test_format_task_start(self, formatter):
        """Test task start formatting"""
        # With description
        message, level = formatter.format_task_start("エラー修正")
        assert message == "🔧 タスク開始: エラー修正"
        assert level == NotificationLevel.CHANNEL

        # Without description
        message, level = formatter.format_task_start(None)
        assert message == "🔧 タスク開始"
        assert level == NotificationLevel.THREAD

    def test_format_file_operation(self, formatter):
        """Test file operation formatting"""
        # Edit operation
        message, level = formatter.format_file_operation(
            "Edit", "/home/user/project/main.py", "/home/user/project"
        )
        assert message == "📝 ファイル編集: `main.py`"
        assert level == NotificationLevel.THREAD

        # Write operation
        message, level = formatter.format_file_operation(
            "Write", "/home/user/project/new_file.py", "/home/user/project"
        )
        assert message == "📝 ファイル作成: `new_file.py`"
        assert level == NotificationLevel.THREAD

        # MultiEdit operation
        message, level = formatter.format_file_operation(
            "MultiEdit", "/home/user/project/config.py", "/home/user/project"
        )
        assert message == "📝 ファイル編集: `config.py`"
        assert level == NotificationLevel.THREAD

        # Unknown operation (fallback to lowercase)
        message, level = formatter.format_file_operation(
            "SomeOtherTool", "/home/user/project/test.py", "/home/user/project"
        )
        assert message == "📝 ファイルsomeothertool: `test.py`"
        assert level == NotificationLevel.THREAD

    def test_format_todo_update(self, formatter):
        """Test todo update formatting"""
        todos = [
            {"status": "completed", "content": "Fix bug"},
            {"status": "pending", "content": "Add test"},
        ]
        message, level = formatter.format_todo_update(todos)
        assert ":white_check_mark: Fix bug" in message
        assert ":ballot_box_with_check: Add test" in message
        assert level == NotificationLevel.THREAD
