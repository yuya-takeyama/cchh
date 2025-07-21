"""Test cases for Zunda speaker"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.types import HookEvent
from src.zunda.config import ZundaspeakStyle
from src.zunda.speaker import ZundaSpeaker


@pytest.fixture
def zunda_speaker():
    """Create ZundaSpeaker instance"""
    with patch("src.zunda.speaker.zunda_config") as mock_config:
        mock_config.enabled = True
        mock_config.default_style = MagicMock(value="0")
        mock_config.is_silent_command = MagicMock(return_value=False)
        speaker = ZundaSpeaker()
        speaker._is_test_environment = lambda: False
        return speaker


@pytest.fixture
def mock_event():
    """Create a mock HookEvent"""
    return HookEvent(
        hook_event_name="PreToolUse",
        session_id="test-session-123",
        cwd="/test/directory",
        tool_name="Bash",
        tool_input={"command": "npm test"},
    )


class TestZundaSpeaker:
    """Test cases for ZundaSpeaker"""

    def test_disabled_speaker(self, zunda_speaker, mock_event):
        """Test that disabled speaker doesn't speak"""
        zunda_speaker.enabled = False
        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(mock_event)
            mock_run.assert_not_called()

    def test_handle_pre_tool_use_bash(self, zunda_speaker):
        """Test handling of Bash command"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Bash",
            tool_input={"command": "npm run test"},
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "エヌピーエム" in args[3]
            assert "run" in args[3]

    def test_handle_pre_tool_use_task(self, zunda_speaker):
        """Test handling of Task tool"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Task",
            tool_input={"description": "Fix authentication"},
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "タスク" in args[3]
            assert "Fix authentication" in args[3]
            assert "実行" in args[3]

    def test_skip_todo_write(self, zunda_speaker):
        """Test that TodoWrite is skipped"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="TodoWrite",
            tool_input={"todos": []},
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)
            mock_run.assert_not_called()

    def test_skip_silent_commands(self, zunda_speaker):
        """Test that silent commands like git diff are skipped in Zunda"""
        silent_commands = ["git status", "git log", "git diff", "ls", "pwd", "cat"]

        for cmd in silent_commands:
            event = HookEvent(
                hook_event_name="PreToolUse",
                session_id="test-session",
                cwd="/test",
                tool_name="Bash",
                tool_input={"command": cmd},
            )

            with patch("subprocess.run") as mock_run:
                zunda_speaker.handle_event(event)
                mock_run.assert_not_called()  # Silent command should not trigger speech

    def test_non_silent_commands_are_spoken(self, zunda_speaker):
        """Test that non-silent commands are still spoken"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Bash",
            tool_input={"command": "git commit -m 'test'"},
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "git commit" in args[3]

    def test_handle_web_fetch(self, zunda_speaker):
        """Test handling of WebFetch operations"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="WebFetch",
            tool_input={"url": "https://example.com/article", "prompt": "Test prompt"},
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ウェブサイトexample.comをチェックするのだ" == args[3]

    def test_handle_notification_permission(self, zunda_speaker):
        """Test handling of permission notifications"""
        event = HookEvent(
            hook_event_name="Notification",
            session_id="test-session",
            cwd="/test",
            notification="Claude needs your permission to use Bash",
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[2] == str(
                ZundaspeakStyle.AMAAMA.value
            )  # Should use AMAAMA style
            assert "許可" in args[3]

    def test_handle_notification_fetch_permission(self, zunda_speaker):
        """Test handling of Fetch permission notifications"""
        event = HookEvent(
            hook_event_name="Notification",
            session_id="test-session",
            cwd="/test",
            notification="Claude needs your permission to use Fetch",
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[2] == str(ZundaspeakStyle.AMAAMA.value)
            assert "Webアクセスの許可が欲しいのだ" == args[3]

    def test_handle_stop_event(self, zunda_speaker):
        """Test handling of stop event"""
        event = HookEvent(
            hook_event_name="Stop",
            session_id="test-session",
            cwd="/test",
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[2] == str(ZundaspeakStyle.SEXY.value)  # Should use SEXY style
            assert "終わった" in args[3]

    def test_speak_exception_handling(self, zunda_speaker):
        """Test that exceptions are handled gracefully"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command not found")

            # Should not raise
            zunda_speaker._speak("Test message")

    def test_command_simplification(self, zunda_speaker):
        """Test command simplification"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Bash",
            tool_input={
                "command": "git commit -m 'Fix issue #123: Authentication not working properly'"
            },
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            args = mock_run.call_args[0][0]
            message = args[3]
            assert "git" in message
            assert "commit" in message
            # Long commit message should be simplified
            assert "Fix issue #123" not in message

    def test_skip_file_operations(self, zunda_speaker):
        """Test that file operations are skipped"""
        file_tools = ["Write", "Edit", "MultiEdit", "Read"]

        for tool in file_tools:
            event = HookEvent(
                hook_event_name="PreToolUse",
                session_id="test-session",
                cwd="/test",
                tool_name=tool,
                tool_input={"file_path": "/test/file.py"},
            )

            with patch("subprocess.run") as mock_run:
                zunda_speaker.handle_event(event)
                mock_run.assert_not_called()

    def test_different_events_ignored(self, zunda_speaker):
        """Test that irrelevant events are ignored"""
        event = HookEvent(
            hook_event_name="PostToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Bash",
            result={"output": "Success"},
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)
            mock_run.assert_not_called()

    def test_disabled_via_env(self):
        """Test that speaker can be disabled via environment"""
        with patch.dict(
            os.environ, {"CCHH_ZUNDA_SPEAKER_ENABLED": "false"}, clear=True
        ):
            # Need to re-import the config to pick up the environment variable
            with patch("src.zunda.speaker.zunda_config") as mock_config:
                mock_config.enabled = False
                speaker = ZundaSpeaker()
                assert not speaker.enabled

    def test_handle_pre_compact(self, zunda_speaker):
        """Test handling of PreCompact event"""
        event = HookEvent(
            hook_event_name="PreCompact",
            session_id="test-session",
            cwd="/test",
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "コンテキストが長くなってきたのだ" in args[3]
            assert "新しいセッション" in args[3]

    def test_git_commands_formatting(self, zunda_speaker):
        """Test various git commands are formatted correctly"""
        git_commands = [
            ("git status", "git status"),
            ("git push origin main", "git push"),
            ("git pull", "git pull"),
            ("git checkout -b feature", "git checkout"),
        ]

        for cmd, expected_phrase in git_commands:
            event = HookEvent(
                hook_event_name="PreToolUse",
                session_id="test-session",
                cwd="/test",
                tool_name="Bash",
                tool_input={"command": cmd},
            )

            with patch("subprocess.run") as mock_run:
                zunda_speaker.handle_event(event)

                if mock_run.call_count > 0:
                    args = mock_run.call_args[0][0]
                    message = args[3]
                    assert expected_phrase in message, (
                        f"Expected '{expected_phrase}' in '{message}'"
                    )

    def test_uv_commands_formatting(self, zunda_speaker):
        """Test various uv commands are formatted correctly"""
        uv_commands = [
            ("uv run task test", "uv run task test"),
            ("uv run task build", "uv run task build"),
            ("uv run pytest", "uv run pytest"),
            ("uv run mypy src", "uv run mypy"),
            ("uv sync", "uv sync"),
            ("uv add requests", "uv add"),
            ("uv pip install numpy", "uv pip"),
        ]

        for command, expected_formatted in uv_commands:
            event = HookEvent(
                hook_event_name="PreToolUse",
                session_id="test-session",
                cwd="/test",
                tool_name="Bash",
                tool_input={"command": command},
            )

            with patch("subprocess.run") as mock_run:
                zunda_speaker.handle_event(event)
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                message = args[3]
                # Check that the formatted command contains expected text
                assert expected_formatted in message, (
                    f"Expected '{expected_formatted}' in '{message}'"
                )

    def test_message_sanitization_security(self, zunda_speaker):
        """Test message sanitization against command injection"""
        # Test dangerous shell characters are removed
        dangerous_message = "hello; rm -rf /; echo evil"
        sanitized = zunda_speaker._sanitize_message(dangerous_message)
        assert ";" not in sanitized  # Shell separator should be removed
        # Now -rf and / are allowed (added to whitelist for command readability)
        expected = "hello rm -rf / echo evil"  # Dangerous ; removed, safe chars remain
        assert sanitized == expected

        # Test control characters are removed
        control_chars = "hello\x00\x01\x02\x03\x07\x1b[31mworld"
        sanitized = zunda_speaker._sanitize_message(control_chars)
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x1b" not in sanitized
        # [] are in whitelist for command use, so [31m remains (but \x1b is removed)
        assert sanitized == "hello[31mworld"

        # Test length limitation
        long_message = "A" * 1500
        sanitized = zunda_speaker._sanitize_message(long_message)
        assert len(sanitized) == 1000

        # Test Japanese characters are preserved
        japanese_message = "こんにちは世界！Hello World 123"
        sanitized = zunda_speaker._sanitize_message(japanese_message)
        assert sanitized == "こんにちは世界！Hello World 123"

        # Test whitespace normalization
        messy_whitespace = "   hello   \t\n  world   "
        sanitized = zunda_speaker._sanitize_message(messy_whitespace)
        assert sanitized == "hello world"

    def test_sanitization_applied_to_speech(self, zunda_speaker):
        """Test that sanitization is applied when speaking"""
        dangerous_message = "safe text; rm -rf /"

        with patch("subprocess.run") as mock_run:
            zunda_speaker._speak(dangerous_message)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            # Verify the message argument (4th position) is sanitized
            actual_message = args[3]
            assert ";" not in actual_message  # Dangerous ; should be removed
            assert "rm" in actual_message  # Safe letters should remain
            assert actual_message == "safe text rm -rf /"

    def test_empty_or_invalid_messages(self, zunda_speaker):
        """Test handling of empty or invalid messages"""
        with patch("subprocess.run") as mock_run:
            # Empty message should not call subprocess
            zunda_speaker._speak("")
            mock_run.assert_not_called()

            # Message that becomes empty after sanitization
            zunda_speaker._speak("\x00\x01\x02")
            mock_run.assert_not_called()

            # Reset mock for valid message test
            mock_run.reset_mock()
            zunda_speaker._speak("valid message")
            mock_run.assert_called_once()

    def test_command_readability_preserved(self, zunda_speaker):
        """Test that common command patterns remain readable after sanitization"""
        command_examples = [
            (
                "git commit -m 'fix: update config'",
                "git commit -m 'fix: update config'",
            ),
            ("npm run build --production", "npm run build --production"),
            ("docker run -p 8080:80 nginx", "docker run -p 8080:80 nginx"),
            ("ls -la /home/user/", "ls -la /home/user/"),
            ("grep -r 'pattern' src/", "grep -r 'pattern' src/"),
        ]

        for original, expected in command_examples:
            sanitized = zunda_speaker._sanitize_message(original)
            assert sanitized == expected, f"Failed for: {original}"
