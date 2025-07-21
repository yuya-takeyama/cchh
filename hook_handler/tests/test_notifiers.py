"""Test cases for notification handlers"""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from hook_handler.config import NotificationLevel, ZundaspeakStyle
from hook_handler.notifiers import SlackNotifier, ZundaspeakNotifier


@pytest.fixture
def slack_notifier():
    """Create SlackNotifier instance"""
    return SlackNotifier()


@patch("hook_handler.notifiers.is_test_environment")
def test_should_send_test_env(mock_is_test, slack_notifier):
    """Test should_send in test environment"""
    mock_is_test.return_value = True
    assert not slack_notifier.should_send()


@patch("hook_handler.notifiers.is_test_environment")
@patch("hook_handler.notifiers.settings")
def test_should_send_disabled(mock_settings, mock_is_test, slack_notifier):
    """Test should_send when disabled"""
    mock_is_test.return_value = False
    mock_settings.slack_enabled = False
    assert not slack_notifier.should_send()


@patch("hook_handler.notifiers.is_test_environment")
@patch("hook_handler.notifiers.settings")
def test_should_send_missing_config(mock_settings, mock_is_test, slack_notifier):
    """Test should_send with missing configuration"""
    mock_is_test.return_value = False
    mock_settings.slack_enabled = True
    mock_settings.slack_configured = False
    assert not slack_notifier.should_send()


@patch("hook_handler.notifiers.is_test_environment")
@patch("hook_handler.notifiers.settings")
def test_should_send_success(mock_settings, mock_is_test, slack_notifier):
    """Test should_send when properly configured"""
    mock_is_test.return_value = False
    mock_settings.slack_enabled = True
    mock_settings.slack_configured = True
    assert slack_notifier.should_send()


@patch("hook_handler.notifiers.SlackNotifier.should_send")
def test_notify_disabled(mock_should_send, slack_notifier):
    """Test notify when disabled"""
    mock_should_send.return_value = False
    result = slack_notifier.notify("Test message")
    assert result is None


@patch("urllib.request.urlopen")
@patch("hook_handler.notifiers.SlackNotifier.should_send")
@patch("hook_handler.notifiers.settings")
def test_notify_success(mock_settings, mock_should_send, mock_urlopen, slack_notifier):
    """Test successful notification"""
    mock_should_send.return_value = True
    mock_settings.slack_bot_token = "xoxb-test-token"
    mock_settings.slack_channel_id = "C1234567890"

    # Mock successful response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"ok": true, "ts": "1234567890.123456"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = slack_notifier.notify("Test message")
    assert result == "1234567890.123456"
    mock_urlopen.assert_called_once()


@patch("urllib.request.urlopen")
@patch("hook_handler.notifiers.SlackNotifier.should_send")
@patch("hook_handler.notifiers.settings")
@patch("sys.stderr", new_callable=StringIO)
def test_notify_api_error(
    mock_stderr, mock_settings, mock_should_send, mock_urlopen, slack_notifier
):
    """Test API error handling"""
    mock_should_send.return_value = True
    mock_settings.slack_bot_token = "xoxb-test-token"
    mock_settings.slack_channel_id = "C1234567890"

    # Mock error response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"ok": false, "error": "channel_not_found"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    result = slack_notifier.notify("Test message")
    assert result is None
    assert "channel_not_found" in mock_stderr.getvalue()


@patch("urllib.request.urlopen")
@patch("hook_handler.notifiers.SlackNotifier.should_send")
@patch("hook_handler.notifiers.settings")
@patch("sys.stderr", new_callable=StringIO)
def test_notify_exception(
    mock_stderr, mock_settings, mock_should_send, mock_urlopen, slack_notifier
):
    """Test exception handling"""
    mock_should_send.return_value = True
    mock_settings.slack_bot_token = "xoxb-test-token"
    mock_settings.slack_channel_id = "C1234567890"

    # Mock exception
    mock_urlopen.side_effect = Exception("Network error")

    result = slack_notifier.notify("Test message")
    assert result is None
    assert "Network error" in mock_stderr.getvalue()


@patch("urllib.request.urlopen")
@patch("hook_handler.notifiers.SlackNotifier.should_send")
@patch("hook_handler.notifiers.settings")
def test_notify_with_thread(
    mock_settings, mock_should_send, mock_urlopen, slack_notifier
):
    """Test notification with thread"""
    mock_should_send.return_value = True
    mock_settings.slack_bot_token = "xoxb-test-token"
    mock_settings.slack_channel_id = "C1234567890"

    # Mock successful response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"ok": true}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    # Mock session manager with thread
    mock_session_manager = MagicMock()
    mock_session_manager.load_state.return_value = {"thread_ts": "thread.123456"}

    slack_notifier.notify(
        "Test message",
        level=NotificationLevel.THREAD,
        session_manager=mock_session_manager,
    )

    # Check that thread_ts was included in request
    request = mock_urlopen.call_args[0][0]
    data = json.loads(request.data.decode("utf-8"))
    assert data["thread_ts"] == "thread.123456"


@patch("urllib.request.urlopen")
@patch("hook_handler.notifiers.SlackNotifier.should_send")
@patch("hook_handler.notifiers.settings")
def test_notify_broadcast(
    mock_settings, mock_should_send, mock_urlopen, slack_notifier
):
    """Test broadcast notification"""
    mock_should_send.return_value = True
    mock_settings.slack_bot_token = "xoxb-test-token"
    mock_settings.slack_channel_id = "C1234567890"

    # Mock successful response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"ok": true}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    slack_notifier.notify("Test message", broadcast=True)

    # Check that reply_broadcast was included
    request = mock_urlopen.call_args[0][0]
    data = json.loads(request.data.decode("utf-8"))
    assert data["reply_broadcast"] == "true"


@pytest.fixture
def zunda_notifier():
    """Create ZundaspeakNotifier instance"""
    return ZundaspeakNotifier()


@patch("subprocess.run")
def test_zunda_notify_success(mock_run, zunda_notifier):
    """Test successful voice notification"""
    zunda_notifier.notify("テストメッセージ", style=ZundaspeakStyle.TSUNTSUN.value)
    mock_run.assert_called_once_with(
        ["zundaspeak", "-s", "2", "テストメッセージ"], capture_output=True
    )


@patch("subprocess.run")
def test_notify_default_style(mock_run, zunda_notifier):
    """Test notification with default style"""
    zunda_notifier.notify("テストメッセージ")
    mock_run.assert_called_once_with(
        ["zundaspeak", "-s", "0", "テストメッセージ"], capture_output=True
    )


@patch("subprocess.run")
def test_zunda_notify_exception(mock_run, zunda_notifier):
    """Test exception handling"""
    mock_run.side_effect = Exception("Command not found")
    # Should not raise exception
    zunda_notifier.notify("テストメッセージ")
