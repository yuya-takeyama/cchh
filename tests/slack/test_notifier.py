"""Test cases for Slack notifier"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.types import HookEvent
from src.slack.config import NotificationLevel, RuntimeConfig
from src.slack.notifier import SlackNotifier


@pytest.fixture
def slack_notifier(tmp_path):
    """Create SlackNotifier instance with test configuration"""
    # Create test configuration (not dependent on environment variables)
    test_config = RuntimeConfig(
        is_test_environment=False,  # Explicitly set to False for testing
        notifications_enabled=True,
        show_session_start=True,
        notify_on_tool_use=True,
        notify_on_stop=True,
        bot_token="xoxb-test-token",
        channel_id="C1234567890",
        command_max_length=200,
        thread_dir=tmp_path / "test_threads",
    )

    # Create notifier with test configuration
    notifier = SlackNotifier(config=test_config)

    # Mock _get_session_tracker to return tracker with is_new_session=False
    def mock_get_session_tracker(session_id):
        mock_tracker = MagicMock()
        mock_tracker.is_new_session = False
        mock_tracker.session_id = session_id
        return mock_tracker

    notifier._get_session_tracker = mock_get_session_tracker
    return notifier


@pytest.fixture
def mock_event():
    """Create a mock HookEvent"""
    return HookEvent(
        hook_event_name="PreToolUse",
        session_id="test-session-123",
        cwd="/test/directory",
        tool_name="Bash",
        tool_input={"command": "echo test"},
        result=None,
        notification=None,
        prompt=None,
    )


class TestSlackNotifier:
    """Test cases for SlackNotifier"""

    def setup_method(self):
        """Setup before each test"""
        # Store original TEST_ENVIRONMENT value
        self.original_test_env = os.environ.get("CCHH_TEST_ENVIRONMENT")

    def teardown_method(self):
        """Cleanup after each test"""
        # Restore original TEST_ENVIRONMENT value
        if self.original_test_env is None:
            os.environ.pop("CCHH_TEST_ENVIRONMENT", None)
        else:
            os.environ["CCHH_TEST_ENVIRONMENT"] = self.original_test_env

    def test_disabled_notifier(self, slack_notifier, mock_event):
        """Test that disabled notifier doesn't send notifications"""
        slack_notifier.config.notifications_enabled = False
        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(mock_event)
            mock_send.assert_not_called()

    def test_unconfigured_notifier(self, tmp_path, mock_event):
        """Test that unconfigured notifier doesn't send notifications"""
        # Create a new notifier with unconfigured state
        unconfigured_config = RuntimeConfig(
            is_test_environment=False,
            notifications_enabled=True,
            show_session_start=True,
            notify_on_tool_use=True,
            notify_on_stop=True,
            bot_token=None,  # No token means unconfigured
            channel_id=None,  # No channel means unconfigured
            command_max_length=200,
            thread_dir=tmp_path / "test_threads",
        )

        notifier = SlackNotifier(config=unconfigured_config)
        with patch.object(notifier, "_send_notification") as mock_send:
            notifier.handle_event(mock_event)
            mock_send.assert_not_called()

    def test_test_environment(self, slack_notifier, mock_event):
        """Test that notifications are skipped in test environment"""
        # Set test environment flag
        slack_notifier.config.is_test_environment = True
        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(mock_event)
            mock_send.assert_not_called()

    def test_new_session_start(self, slack_notifier):
        """Test handling of new session"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="new-session-456",
            cwd="/new/directory",
            tool_name="Bash",
            tool_input={"command": "git commit -m 'test'"},
        )

        # Mock session tracker to have a new session
        mock_tracker = MagicMock()
        mock_tracker.is_new_session = True

        with patch.object(
            slack_notifier, "_get_session_tracker", return_value=mock_tracker
        ):
            with patch.object(slack_notifier, "_send_notification") as mock_send:
                slack_notifier.handle_event(event)

                # Should send two messages: session start and command
                calls = mock_send.call_args_list
                assert len(calls) >= 2
                # First call should be session start
                assert ":clapper:" in calls[0][0][0]  # session start message
                assert "new-ses" in calls[0][0][0]  # truncated session ID
                # Second call should be command notification
                assert "git commit" in calls[1][0][0]  # command message

    def test_handle_bash_command(self, slack_notifier):
        """Test handling of Bash tool"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="bash-test-session",
            cwd="/test/directory",
            tool_name="Bash",
            tool_input={"command": "npm install"},
        )

        # Mock session tracker to avoid filesystem access
        mock_tracker = MagicMock()
        mock_tracker.is_new_session = (
            False  # Not a new session, so no session start message
        )

        with patch.object(
            slack_notifier, "_get_session_tracker", return_value=mock_tracker
        ):
            with patch.object(slack_notifier, "_send_notification") as mock_send:
                slack_notifier.handle_event(event)

                # Should send command notification
                mock_send.assert_called()
                # Get the actual call
                args = mock_send.call_args[0]
                assert "npm install" in args[0], (
                    f"Command not found in message: {args[0]}"
                )

    def test_skip_silent_commands(self, slack_notifier):
        """Test that silent commands are skipped"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Bash",
            tool_input={"command": "git status"},
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            # git status should be skipped
            mock_send.assert_not_called()

    def test_handle_task_tool(self, slack_notifier):
        """Test handling of Task tool"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Task",
            tool_input={"description": "Fix authentication bug"},
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "Fix authentication bug" in args[0]

    def test_handle_todo_write(self, slack_notifier):
        """Test handling of TodoWrite tool"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="TodoWrite",
            tool_input={
                "todos": [
                    {"content": "Task 1", "status": "completed", "priority": "high"},
                    {"content": "Task 2", "status": "pending", "priority": "medium"},
                ]
            },
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "Task 1" in args[0]
            assert "Task 2" in args[0]

    def test_handle_file_operation(self, slack_notifier):
        """Test handling of file operations"""
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Write",
            tool_input={"file_path": "/test/file.py"},
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "file.py" in args[0]

    def test_handle_post_tool_error(self, slack_notifier):
        """Test handling of tool errors"""
        event = HookEvent(
            hook_event_name="PostToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Bash",
            tool_input=None,
            result={"error": "Command failed with exit code 1"},
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "❌" in args[0]
            assert "Command failed" in args[0]
            assert args[1] == NotificationLevel.CHANNEL  # Error should be high priority

    def test_handle_task_completion(self, slack_notifier):
        """Test handling of task completion"""
        event = HookEvent(
            hook_event_name="PostToolUse",
            session_id="test-session",
            cwd="/test",
            tool_name="Task",
            tool_input=None,
            result={"success": True},
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "✅" in args[0]
            assert "タスク完了" in args[0]

    def test_handle_notification_permission(self, slack_notifier):
        """Test handling of permission notifications"""
        event = HookEvent(
            hook_event_name="Notification",
            session_id="test-session",
            cwd="/test",
            notification="Claude needs your permission to use Bash",
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "🔐" in args[0]
            assert "Bash" in args[0]

    def test_handle_stop_event(self, slack_notifier):
        """Test handling of stop event"""
        event = HookEvent(
            hook_event_name="Stop",
            session_id="test-session",
            cwd="/test",
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "🛑" in args[0]

    def test_handle_user_prompt(self, slack_notifier):
        """Test handling of user prompt"""
        event = HookEvent(
            hook_event_name="UserPromptSubmit",
            session_id="test-session",
            cwd="/test",
            prompt="Please fix the authentication bug",
        )

        with patch.object(slack_notifier, "_send_notification") as mock_send:
            slack_notifier.handle_event(event)

            mock_send.assert_called()
            args = mock_send.call_args[0]
            assert "fix the authentication" in args[0]
            kwargs = mock_send.call_args[1]
            assert kwargs.get("broadcast") is True

    @patch("urllib.request.urlopen")
    def test_send_notification_success(self, mock_urlopen, slack_notifier):
        """Test successful notification sending"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ok": true, "ts": "1234567890.123456"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        session_tracker = slack_notifier._get_session_tracker("test-session")
        result = slack_notifier._send_notification(
            "Test message", NotificationLevel.CHANNEL, session_tracker, "/test"
        )

        assert result == "1234567890.123456"
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_send_notification_api_error(self, mock_urlopen, slack_notifier, capsys):
        """Test API error handling"""
        # Mock error response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ok": false, "error": "channel_not_found"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        session_tracker = slack_notifier._get_session_tracker("test-session")
        result = slack_notifier._send_notification(
            "Test message", NotificationLevel.CHANNEL, session_tracker, "/test"
        )

        assert result is None
        captured = capsys.readouterr()
        assert "channel_not_found" in captured.err

    @patch("urllib.request.urlopen")
    def test_send_notification_exception(self, mock_urlopen, slack_notifier, capsys):
        """Test exception handling"""
        # Mock exception
        mock_urlopen.side_effect = Exception("Network error")

        session_tracker = slack_notifier._get_session_tracker("test-session")
        result = slack_notifier._send_notification(
            "Test message", NotificationLevel.CHANNEL, session_tracker, "/test"
        )

        assert result is None
        captured = capsys.readouterr()
        assert "Network error" in captured.err

    def test_thread_state_persistence(self, slack_notifier, tmp_path):
        """Test thread state saving and loading"""
        slack_notifier.config.thread_dir = tmp_path

        # Save thread state
        slack_notifier._save_thread_state("test-session", "1234567890.123456")

        # Load thread state
        state = slack_notifier._load_thread_state("test-session")
        assert state == {"thread_ts": "1234567890.123456"}

    @patch("urllib.request.urlopen")
    def test_thread_continuation(self, mock_urlopen, slack_notifier, tmp_path):
        """Test that messages continue in the same thread"""
        slack_notifier.config.thread_dir = tmp_path

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ok": true, "ts": "1234567890.123456"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        session_tracker = slack_notifier._get_session_tracker("test-session")

        # First message creates thread
        slack_notifier._send_notification(
            "First message", NotificationLevel.CHANNEL, session_tracker, "/test"
        )

        # Check thread state was saved
        thread_state = slack_notifier._load_thread_state("test-session")
        assert thread_state == {"thread_ts": "1234567890.123456"}

        # Second message should use thread
        slack_notifier._send_notification(
            "Second message", NotificationLevel.THREAD, session_tracker, "/test"
        )

        # Check second request includes thread_ts
        second_call = mock_urlopen.call_args_list[1]
        request = second_call[0][0]
        data = json.loads(request.data.decode("utf-8"))
        assert data.get("thread_ts") == "1234567890.123456"

    def test_should_handle_event_notifications_disabled(self, tmp_path):
        """Test should_handle_event with notifications disabled"""
        config = RuntimeConfig(
            is_test_environment=False,
            notifications_enabled=False,  # Disabled
            show_session_start=True,
            notify_on_tool_use=True,
            notify_on_stop=True,
            bot_token="xoxb-test-token",
            channel_id="C1234567890",
            command_max_length=200,
            thread_dir=tmp_path / "test_threads",
        )
        notifier = SlackNotifier(config=config)
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
        )
        assert notifier.should_handle_event(event) is False

    def test_should_handle_event_not_configured(self, tmp_path):
        """Test should_handle_event with missing configuration"""
        config = RuntimeConfig(
            is_test_environment=False,
            notifications_enabled=True,
            show_session_start=True,
            notify_on_tool_use=True,
            notify_on_stop=True,
            bot_token=None,  # Not configured
            channel_id=None,  # Not configured
            command_max_length=200,
            thread_dir=tmp_path / "test_threads",
        )
        notifier = SlackNotifier(config=config)
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
        )
        assert notifier.should_handle_event(event) is False

    def test_should_handle_event_test_environment(self, tmp_path):
        """Test should_handle_event in test environment"""
        config = RuntimeConfig(
            is_test_environment=True,  # Test environment
            notifications_enabled=True,
            show_session_start=True,
            notify_on_tool_use=True,
            notify_on_stop=True,
            bot_token="xoxb-test-token",
            channel_id="C1234567890",
            command_max_length=200,
            thread_dir=tmp_path / "test_threads",
        )
        notifier = SlackNotifier(config=config)
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
        )
        assert notifier.should_handle_event(event) is False

    def test_should_handle_event_all_conditions_met(self, tmp_path):
        """Test should_handle_event when all conditions are met"""
        config = RuntimeConfig(
            is_test_environment=False,
            notifications_enabled=True,
            show_session_start=True,
            notify_on_tool_use=True,
            notify_on_stop=True,
            bot_token="xoxb-test-token",
            channel_id="C1234567890",
            command_max_length=200,
            thread_dir=tmp_path / "test_threads",
        )
        notifier = SlackNotifier(config=config)
        event = HookEvent(
            hook_event_name="PreToolUse",
            session_id="test-session",
            cwd="/test",
        )
        assert notifier.should_handle_event(event) is True
