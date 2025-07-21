"""Test cases for event dispatcher"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.dispatcher import EventDispatcher
from src.core.types import HookEvent


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


class TestEventDispatcher:
    """Test cases for EventDispatcher"""

    @patch.dict(os.environ, {"CCHH_SLACK_NOTIFICATIONS_ENABLED": "false"})
    @patch.dict(os.environ, {"CCHH_ZUNDA_SPEAKER_ENABLED": "false"})
    @patch.dict(os.environ, {"CCHH_EVENT_LOGGING_ENABLED": "false"})
    def test_all_features_disabled(self):
        """Test dispatcher with all features disabled"""
        dispatcher = EventDispatcher()
        assert dispatcher.slack is None
        assert dispatcher.zunda is None
        assert dispatcher.logger is None

    @patch("src.slack.notifier.SlackNotifier")
    @patch.dict(os.environ, {"CCHH_SLACK_NOTIFICATIONS_ENABLED": "true"})
    def test_slack_enabled(self, mock_slack_class):
        """Test dispatcher with Slack enabled"""
        mock_slack = MagicMock()
        mock_slack_class.return_value = mock_slack

        dispatcher = EventDispatcher()
        assert dispatcher.slack is mock_slack

    @patch("src.zunda.speaker.ZundaSpeaker")
    @patch.dict(os.environ, {"CCHH_ZUNDA_SPEAKER_ENABLED": "true"})
    def test_zunda_enabled(self, mock_zunda_class):
        """Test dispatcher with Zunda enabled"""
        mock_zunda = MagicMock()
        mock_zunda_class.return_value = mock_zunda

        dispatcher = EventDispatcher()
        assert dispatcher.zunda is mock_zunda

    @patch("src.logger.event_logger.EventLogger")
    @patch.dict(os.environ, {"CCHH_EVENT_LOGGING_ENABLED": "true"})
    def test_logger_enabled(self, mock_logger_class):
        """Test dispatcher with Logger enabled"""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        dispatcher = EventDispatcher()
        assert dispatcher.logger is mock_logger

    def test_dispatch_calls_all_handlers(self, mock_event):
        """Test that dispatch calls all enabled handlers"""
        dispatcher = EventDispatcher()

        # Mock all handlers
        dispatcher.slack = MagicMock()
        dispatcher.zunda = MagicMock()
        dispatcher.logger = MagicMock()

        dispatcher.dispatch(mock_event)

        # Verify all handlers were called
        dispatcher.slack.handle_event.assert_called_once_with(mock_event)
        dispatcher.zunda.handle_event.assert_called_once_with(mock_event)
        dispatcher.logger.handle_event.assert_called_once_with(mock_event)

    def test_dispatch_handles_slack_error(self, mock_event, capsys):
        """Test that dispatch continues if Slack handler fails"""
        dispatcher = EventDispatcher()

        # Mock handlers
        dispatcher.slack = MagicMock()
        dispatcher.slack.handle_event.side_effect = Exception("Slack error")
        dispatcher.zunda = MagicMock()
        dispatcher.logger = MagicMock()

        dispatcher.dispatch(mock_event)

        # Verify other handlers were still called
        dispatcher.zunda.handle_event.assert_called_once_with(mock_event)
        dispatcher.logger.handle_event.assert_called_once_with(mock_event)

        # Check error was printed
        captured = capsys.readouterr()
        assert "Slack handler error: Slack error" in captured.out

    def test_dispatch_handles_all_errors(self, mock_event, capsys):
        """Test that dispatch handles errors from all handlers"""
        dispatcher = EventDispatcher()

        # Mock all handlers to fail
        dispatcher.slack = MagicMock()
        dispatcher.slack.handle_event.side_effect = Exception("Slack error")
        dispatcher.zunda = MagicMock()
        dispatcher.zunda.handle_event.side_effect = Exception("Zunda error")
        dispatcher.logger = MagicMock()
        dispatcher.logger.handle_event.side_effect = Exception("Logger error")

        # Should not raise
        dispatcher.dispatch(mock_event)

        # Check all errors were printed
        captured = capsys.readouterr()
        assert "Slack handler error: Slack error" in captured.out
        assert "Zunda handler error: Zunda error" in captured.out
        assert "Logger handler error: Logger error" in captured.out

    def test_dispatch_with_none_handlers(self, mock_event):
        """Test dispatch works with None handlers"""
        dispatcher = EventDispatcher()
        dispatcher.slack = None
        dispatcher.zunda = None
        dispatcher.logger = None

        # Should not raise
        dispatcher.dispatch(mock_event)

    @patch("src.slack.notifier.SlackNotifier", side_effect=ImportError)
    @patch.dict(os.environ, {"CCHH_SLACK_NOTIFICATIONS_ENABLED": "true"})
    def test_slack_import_error(self, mock_slack_class, capsys):
        """Test handling of Slack import error"""
        dispatcher = EventDispatcher()
        assert dispatcher.slack is None

        captured = capsys.readouterr()
        assert "Warning: Slack module not found" in captured.out

    @patch("src.zunda.speaker.ZundaSpeaker", side_effect=ImportError)
    @patch.dict(os.environ, {"CCHH_ZUNDA_SPEAKER_ENABLED": "true"})
    def test_zunda_import_error(self, mock_zunda_class, capsys):
        """Test handling of Zunda import error"""
        dispatcher = EventDispatcher()
        assert dispatcher.zunda is None

        captured = capsys.readouterr()
        assert "Warning: Zunda module not found" in captured.out

    @patch("src.logger.event_logger.EventLogger", side_effect=ImportError)
    @patch.dict(os.environ, {"CCHH_EVENT_LOGGING_ENABLED": "true"})
    def test_logger_import_error(self, mock_logger_class, capsys):
        """Test handling of Logger import error"""
        dispatcher = EventDispatcher()
        assert dispatcher.logger is None

        captured = capsys.readouterr()
        assert "Warning: Logger module not found" in captured.out
