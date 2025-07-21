"""Test cases for CommandFormatter"""

import pytest

from src.slack.command_formatter import CommandFormatter


class TestCommandFormatter:
    """Test cases for CommandFormatter"""

    @pytest.fixture
    def formatter(self):
        """Create CommandFormatter instance"""
        return CommandFormatter()

    def test_format_returns_full_command(self, formatter):
        """Test that format() returns the full command without truncation"""
        # Short command
        command = "ls -la"
        assert formatter.format(command) == "ls -la"
        
        # Long command
        long_command = "git commit -m 'This is a very long commit message that would normally be truncated'"
        assert formatter.format(long_command) == long_command
        
        # Multi-line command
        multi_line_command = '''git commit -m "$(cat <<'EOF'
First line
Second line
Third line
EOF
)"'''
        assert formatter.format(multi_line_command) == multi_line_command
        
        # Command with special characters
        special_command = "echo 'Hello $USER! && pwd || exit'"
        assert formatter.format(special_command) == special_command

    def test_format_with_context(self, formatter):
        """Test format_with_context method"""
        command = "npm install"
        
        # With description
        result = formatter.format_with_context(command, "Install dependencies")
        assert result == "Install dependencies: `npm install`"
        
        # Without description
        result = formatter.format_with_context(command)
        assert result == "`npm install`"
        
        # Multi-line command with description
        multi_line = "npm install\n@types/node"
        result = formatter.format_with_context(multi_line, "Install types")
        assert result == "Install types: `npm install\n@types/node`"