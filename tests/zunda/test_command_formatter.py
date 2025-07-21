"""Test cases for CommandFormatter"""

import pytest

from src.zunda.command_formatter import CommandFormatter


class TestCommandFormatter:
    """Test cases for CommandFormatter"""

    @pytest.fixture
    def formatter(self):
        """Create CommandFormatter instance"""
        return CommandFormatter()

    def test_format_commands(self, formatter):
        """Table-driven test for command formatting"""
        test_cases = [
            # Basic commands (no translation)
            ("pwd", "pwd"),
            ("ls", "ls"),
            ("cd /home/user", "cd"),
            ("cat file.txt", "cat"),
            ("rm file.txt", "rm"),
            ("cp src dst", "cp"),
            ("mv old new", "mv"),
            ("mkdir dir", "mkdir"),
            ("touch file", "touch"),
            ("echo hello", "echo"),
            
            # Git commands (no translation)
            ("git status", "git status"),
            ("git add .", "git add"),
            ("git commit -m 'message'", "git commit"),
            ("git push origin main", "git push"),
            ("git pull", "git pull"),
            ("git checkout -b feature", "git checkout"),
            ("git merge develop", "git merge"),
            
            # Package managers (npm and pnpm are translated)
            ("npm install", "エヌピーエム install"),
            ("npm run test", "エヌピーエム run test"),
            ("npm run build", "エヌピーエム run build"),
            ("yarn install", "yarn install"),
            ("yarn run dev", "yarn run dev"),
            ("pnpm install", "ピーエヌピーエム install"),
            ("pnpm run test", "ピーエヌピーエム run test"),
            
            # UV commands - special handling
            ("uv sync", "uv sync"),
            ("uv add requests", "uv add"),
            ("uv run pytest", "uv run pytest"),
            ("uv run mypy src", "uv run mypy"),
            ("uv run task test", "uv run task test"),
            ("uv run task build", "uv run task build"),
            ("uv run task lint --fix", "uv run task lint"),
            
            # Docker commands
            ("docker ps", "docker ps"),
            ("docker run ubuntu", "docker run"),
            ("docker compose up", "docker compose up"),
            
            # GitHub CLI
            ("gh pr create", "gh pr create"),
            ("gh pr list", "gh pr list"),
            ("gh issue create", "gh issue create"),
            ("gh issue list", "gh issue list"),
            
            # Other tools
            ("go mod init", "go mod init"),
            ("cargo build", "cargo build"),
            ("kubectl get pods", "kubectl get"),
            ("terraform plan", "terraform plan"),
            
            # Text editors
            ("vim file.txt", "vim"),
            ("nvim config.lua", "nvim"),
            ("nano README.md", "nano"),
            
            # tsx command (should be translated)
            ("tsx script.ts", "ティーエスエックス"),
            
            # Commands not in dictionary
            ("unknown-cmd arg1 arg2", "unknown-cmd"),
            ("git unknown-subcmd", "git unknown-subcmd"),
            
            # Empty and edge cases
            ("", ""),
        ]
        
        for command, expected in test_cases:
            result = formatter.format(command)
            assert result == expected, f"Command '{command}' should format to '{expected}', but got '{result}'"
    
    def test_parts_limit(self, formatter):
        """Test _get_parts_limit method directly"""
        test_cases = [
            
            # Git commands
            (["git"], 2),
            (["git", "status"], 2),
            (["git", "add", "."], 2),
            (["git", "commit", "-m", "msg"], 2),
            
            # Package managers
            (["npm"], 2),
            (["npm", "install"], 2),
            (["npm", "run"], 3),
            (["npm", "run", "test"], 3),
            (["npm", "run", "test", "--watch"], 3),
            
            # UV special cases
            (["uv"], 2),
            (["uv", "sync"], 2),
            (["uv", "run"], 3),
            (["uv", "run", "pytest"], 3),
            (["uv", "run", "task"], 4),
            (["uv", "run", "task", "test"], 4),
            (["uv", "run", "task", "test", "--verbose"], 4),
            
            # GitHub CLI
            (["gh"], 2),
            (["gh", "pr"], 3),
            (["gh", "pr", "create"], 3),
            (["gh", "issue"], 3),
            (["gh", "issue", "list", "--label", "bug"], 3),
            
            # Unknown commands
            (["unknown"], 1),
            (["unknown", "subcmd"], 1),
        ]
        
        for parts, expected_limit in test_cases:
            result = formatter._get_parts_limit(parts)
            assert result == expected_limit, f"Parts {parts} should have limit {expected_limit}, but got {result}"
    
    def test_word_dictionary_lookup(self, formatter):
        """Test word dictionary lookups"""
        # Test only the translations we have
        assert formatter.words["npm"] == "エヌピーエム"
        assert formatter.words["pnpm"] == "ピーエヌピーエム"
        assert formatter.words["tsx"] == "ティーエスエックス"