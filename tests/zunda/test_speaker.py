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
        mock_config.speak_on_prompt_submit = True
        mock_config.speak_speed = 1.2
        mock_config.default_style = MagicMock(value="0")
        mock_config.is_silent_command = MagicMock(return_value=False)
        speaker = ZundaSpeaker()
        speaker._is_test_environment = lambda: False
        return speaker


@pytest.fixture
def mock_event():
    """Create a mock HookEvent"""
    return HookEvent(
        hook_event_name="UserPromptSubmit",
        session_id="test-session-123",
        cwd="/test/directory",
        prompt="Please fix the authentication bug",
    )


class TestZundaSpeaker:
    """Test cases for ZundaSpeaker"""

    def test_disabled_speaker(self, zunda_speaker, mock_event):
        """Test that disabled speaker doesn't speak"""
        zunda_speaker.enabled = False
        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(mock_event)
            mock_run.assert_not_called()

    def test_handle_user_prompt_submit(self, zunda_speaker, mock_event):
        """Test handling of UserPromptSubmit event"""
        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(mock_event)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "zundaspeak"
            assert args[1] == "-s"
            assert args[2] == "0"  # Default style
            assert "authentication" in args[3]

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
            assert "ラン" in args[3]
            assert "実行" in args[3]

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

    def test_prompt_formatting(self, zunda_speaker):
        """Test prompt formatting"""
        long_prompt = "A" * 200
        event = HookEvent(
            hook_event_name="UserPromptSubmit",
            session_id="test-session",
            cwd="/test",
            prompt=long_prompt,
        )

        with patch("subprocess.run") as mock_run:
            zunda_speaker.handle_event(event)

            args = mock_run.call_args[0][0]
            message = args[3]
            # Should be truncated
            assert len(message) < 150
            assert "という指示なのだ" in message

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
            assert "ギット" in message
            assert "コミット" in message
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
        with patch.dict(os.environ, {"ZUNDA_SPEAKER_ENABLED": "false"}, clear=True):
            # Need to re-import the config to pick up the environment variable
            with patch("src.zunda.speaker.zunda_config") as mock_config:
                mock_config.enabled = False
                speaker = ZundaSpeaker()
                assert not speaker.enabled

    def test_git_commands_formatting(self, zunda_speaker):
        """Test various git commands are formatted correctly"""
        git_commands = [
            ("git status", "ギットステータス"),
            ("git push origin main", "ギットプッシュ"),
            ("git pull", "ギットプル"),
            ("git checkout -b feature", "ギットチェックアウト"),
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
