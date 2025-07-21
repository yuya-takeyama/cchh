"""Test cases for hook event handlers"""

from unittest.mock import MagicMock, patch

import pytest

from hook_handler.config import NotificationLevel, ZundaspeakStyle
from hook_handler.handlers import HookHandler


@pytest.fixture
def handler():
    """Create HookHandler instance with mocked dependencies"""
    session_id = "test-session-123"
    cwd = "/test/directory"

    with patch("hook_handler.handlers.SessionManager") as mock_session_manager_class:
        mock_session_manager = MagicMock()
        mock_session_manager_class.return_value = mock_session_manager

        handler = HookHandler(session_id, cwd)
        handler.mock_session_manager = mock_session_manager  # type: ignore
        yield handler


@patch("hook_handler.handlers.zundaspeak_notifier")
@patch("hook_handler.handlers.slack_notifier")
def test_handle_pre_tool_use_task(mock_slack, mock_zunda, handler):
    """Test PreToolUse for Task tool"""
    data = {
        "tool_name": "Task",
        "tool_input": {"description": "Fix bug in authentication"},
    }

    handler.handle_pre_tool_use(data)

    # Check Zundaspeak was called
    mock_zunda.notify.assert_called_once_with(
        "タスク「Fix bug in authentication」を実行するのだ"
    )

    # Check Slack was called with correct level (important task)
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert "Fix bug" in args[0]
    kwargs = mock_slack.notify.call_args[1]
    assert kwargs["level"] == NotificationLevel.CHANNEL


@patch("hook_handler.handlers.zundaspeak_notifier")
@patch("hook_handler.handlers.slack_notifier")
def test_handle_pre_tool_use_bash(mock_slack, mock_zunda, handler):
    """Test PreToolUse for Bash tool"""
    data = {
        "tool_name": "Bash",
        "tool_input": {"command": 'git commit -m "Fix issue"'},
    }

    handler.handle_pre_tool_use(data)

    # Check Zundaspeak was called
    mock_zunda.notify.assert_called_once()
    args = mock_zunda.notify.call_args[0]
    assert "ギット コミット" in args[0]

    # Check Slack was called (critical command)
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert "git commit" in args[0]
    kwargs = mock_slack.notify.call_args[1]
    assert kwargs["level"] == NotificationLevel.CHANNEL


@patch("hook_handler.handlers.zundaspeak_notifier")
@patch("hook_handler.handlers.slack_notifier")
def test_handle_pre_tool_use_todo(mock_slack, mock_zunda, handler):
    """Test PreToolUse for TodoWrite tool"""
    data = {
        "tool_name": "TodoWrite",
        "tool_input": {
            "todos": [
                {"content": "Task 1", "status": "completed"},
                {"content": "Task 2", "status": "pending"},
            ]
        },
    }

    handler.handle_pre_tool_use(data)

    # Check Zundaspeak was NOT called (TodoWrite is silent)
    mock_zunda.notify.assert_not_called()

    # Check Slack was called with formatted todo list
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert ":white_check_mark: Task 1" in args[0]
    assert ":ballot_box_with_check: Task 2" in args[0]


@patch("hook_handler.handlers.slack_notifier")
def test_handle_post_tool_use_error(mock_slack, handler):
    """Test PostToolUse with error"""
    data = {
        "tool_name": "Bash",
        "result": {"error": "Command failed with exit code 1"},
    }

    handler.handle_post_tool_use(data)

    # Check error notification was sent
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert "❌" in args[0]
    assert "Command failed" in args[0]
    kwargs = mock_slack.notify.call_args[1]
    assert kwargs["level"] == NotificationLevel.CHANNEL


@patch("hook_handler.handlers.slack_notifier")
def test_handle_post_tool_use_task_complete(mock_slack, handler):
    """Test PostToolUse for Task completion"""
    data = {"tool_name": "Task", "result": {}}

    handler.handle_post_tool_use(data)

    # Check completion notification
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert "✅" in args[0]
    assert "タスク完了" in args[0]


@patch("hook_handler.handlers.zundaspeak_notifier")
@patch("hook_handler.handlers.slack_notifier")
def test_handle_notification_permission(mock_slack, mock_zunda, handler):
    """Test notification handler for permission requests"""
    data = {"message": "Claude needs your permission to use Bash"}

    handler.handle_notification(data)

    # Check Zundaspeak
    mock_zunda.notify.assert_called_once_with(
        "コマンドの許可が欲しいのだ", style=ZundaspeakStyle.AMAAMA.value
    )

    # Check Slack (with broadcast)
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert "🔐" in args[0]
    assert "Bash" in args[0]
    kwargs = mock_slack.notify.call_args[1]
    assert kwargs["broadcast"] is True


@patch("hook_handler.handlers.zundaspeak_notifier")
@patch("hook_handler.handlers.slack_notifier")
def test_handle_notification_skip_file_changes(mock_slack, mock_zunda, handler):
    """Test notification skips file modification messages"""
    data = {"message": "File has been modified"}

    handler.handle_notification(data)

    # Should not call any notifiers
    mock_slack.notify.assert_not_called()
    mock_zunda.notify.assert_not_called()


@patch("hook_handler.handlers.zundaspeak_notifier")
@patch("hook_handler.handlers.slack_notifier")
def test_handle_stop(mock_slack, mock_zunda, handler):
    """Test stop handler"""
    handler.handle_stop({})

    # Check Zundaspeak
    mock_zunda.notify.assert_called_once_with(
        "作業が終わったのだ。次は何をするのだ？", style=ZundaspeakStyle.SEXY.value
    )

    # Check Slack (with broadcast)
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert "🛑" in args[0]
    kwargs = mock_slack.notify.call_args[1]
    assert kwargs["broadcast"] is True


@patch("hook_handler.handlers.slack_notifier")
def test_handle_session_start(mock_slack, handler):
    """Test session start handler"""
    handler.handle_session_start()

    # Check Slack notification
    mock_slack.notify.assert_called_once()
    args = mock_slack.notify.call_args[0]
    assert ":clapper:" in args[0]
    assert "test-ses" in args[0]  # session_id[:8]
    assert "/test/directory" in args[0]
