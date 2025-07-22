"""Tests for I/O helper functions"""

import io
import json

import pytest

from src.core.types import HookEventName
from src.utils.io_helpers import _normalize_hook_event_data, load_hook_event


class TestLoadHookEvent:
    """Test cases for load_hook_event function"""

    def test_load_flat_notification_event(self):
        """Test loading flat notification event (backward compatibility)"""
        event_data = {
            "hook_event_name": "Notification",
            "session_id": "test-session-123",
            "cwd": "/test/directory",
            "notification": "Claude needs your permission to use Bash",
        }

        event_json = json.dumps(event_data)
        event = load_hook_event(io.StringIO(event_json))

        assert event.hook_event_name == HookEventName.NOTIFICATION
        assert event.session_id == "test-session-123"
        assert event.cwd == "/test/directory"
        assert event.notification == "Claude needs your permission to use Bash"

    def test_load_nested_notification_event(self):
        """Test loading nested notification event (real Claude Code format)"""
        # Real Claude Code event structure from issue #14
        event_data = {
            "timestamp": "2025-07-22T08:43:46.231704Z",
            "hook_type": "Notification",
            "session_id": "5554b911-618f-476b-abee-384e610a82d7",
            "cwd": "/Users/yuya/src/github.com/yuya-takeyama/cchh",
            "data": {
                "session_id": "5554b911-618f-476b-abee-384e610a82d7",
                "transcript_path": "/Users/yuya/.claude/projects/-Users-yuya-src-github-com-yuya-takeyama-cchh/5554b911-618f-476b-abee-384e610a82d7.jsonl",
                "cwd": "/Users/yuya/src/github.com/yuya-takeyama/cchh",
                "hook_event_name": "Notification",
                "message": "Claude needs your permission to use Fetch",
            },
        }

        event_json = json.dumps(event_data)
        event = load_hook_event(io.StringIO(event_json))

        assert event.hook_event_name == HookEventName.NOTIFICATION
        assert event.session_id == "5554b911-618f-476b-abee-384e610a82d7"
        assert event.cwd == "/Users/yuya/src/github.com/yuya-takeyama/cchh"
        assert event.notification == "Claude needs your permission to use Fetch"

    def test_load_nested_tool_event(self):
        """Test loading nested tool event (other event types)"""
        event_data = {
            "hook_type": "PreToolUse",
            "session_id": "test-session",
            "cwd": "/test",
            "data": {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "echo test"},
            },
        }

        event_json = json.dumps(event_data)
        event = load_hook_event(io.StringIO(event_json))

        assert event.hook_event_name == HookEventName.PRE_TOOL_USE
        assert event.session_id == "test-session"
        assert event.cwd == "/test"
        assert event.tool_name == "Bash"
        assert event.tool_input == {"command": "echo test"}
        assert event.notification is None  # Should not have notification

    def test_missing_hook_event_name(self):
        """Test error handling for missing hook_event_name"""
        event_data = {"session_id": "test-session", "cwd": "/test"}

        event_json = json.dumps(event_data)
        with pytest.raises(ValueError, match="Missing required field: hook_event_name"):
            load_hook_event(io.StringIO(event_json))

    def test_invalid_json(self):
        """Test error handling for invalid JSON"""
        with pytest.raises(json.JSONDecodeError):
            load_hook_event(io.StringIO("invalid json"))

    def test_defaults_applied(self):
        """Test that defaults are applied for missing fields"""
        event_data = {"hook_event_name": "Notification"}

        event_json = json.dumps(event_data)
        event = load_hook_event(io.StringIO(event_json))

        assert event.hook_event_name == HookEventName.NOTIFICATION
        assert event.session_id == "unknown"
        assert event.cwd is not None  # Should be set to current directory


class TestNormalizeHookEventData:
    """Test cases for _normalize_hook_event_data function"""

    def test_flat_data_unchanged(self):
        """Test that flat data structure is unchanged"""
        data = {
            "hook_event_name": "Notification",
            "session_id": "test-session",
            "notification": "Test message",
        }

        result = _normalize_hook_event_data(data)

        assert result == data
        assert result is not data  # Should be a copy

    def test_nested_data_flattened(self):
        """Test that nested data structure is flattened"""
        data = {
            "hook_type": "Notification",
            "session_id": "outer-session",
            "data": {
                "hook_event_name": "Notification",
                "session_id": "inner-session",
                "message": "Test notification",
            },
        }

        result = _normalize_hook_event_data(data)

        # Should contain flattened data
        assert result["hook_event_name"] == "Notification"
        assert result["session_id"] == "inner-session"  # Inner takes precedence
        assert result["notification"] == "Test notification"
        assert result["hook_type"] == "Notification"  # Top-level preserved

    def test_notification_message_mapping(self):
        """Test that message field is mapped to notification for Notification events"""
        data = {
            "data": {
                "hook_event_name": "Notification",
                "message": "Permission required",
            }
        }

        result = _normalize_hook_event_data(data)

        assert result["notification"] == "Permission required"
        assert "message" in result  # Original message should still be there

    def test_non_notification_no_mapping(self):
        """Test that message field is not mapped for non-Notification events"""
        data = {"data": {"hook_event_name": "PreToolUse", "message": "Some message"}}

        result = _normalize_hook_event_data(data)

        assert "notification" not in result
        assert result["message"] == "Some message"

    def test_existing_notification_preserved(self):
        """Test that existing notification field is preserved"""
        data = {
            "data": {
                "hook_event_name": "Notification",
                "message": "Message field",
                "notification": "Notification field",
            }
        }

        result = _normalize_hook_event_data(data)

        # Should preserve existing notification, not override with message
        assert result["notification"] == "Notification field"

    def test_no_data_field_passthrough(self):
        """Test that data without 'data' field passes through unchanged"""
        data = {"hook_event_name": "Stop", "session_id": "test-session"}

        result = _normalize_hook_event_data(data)

        assert result == data
        assert result is not data  # Should be a copy

    def test_non_dict_data_field(self):
        """Test handling of non-dict data field"""
        raw_data = {
            "data": "not a dictionary",
            "hook_event_name": "Notification",
            "session_id": "test-session",
        }

        result = _normalize_hook_event_data(raw_data)

        # Should return original data when data field is not a dict
        assert result == raw_data
        assert result is not raw_data  # Should be a copy

    def test_notification_string_type(self):
        """Test that notification field can be a string type"""
        from src.utils.io_helpers import load_hook_event

        # Test with string notification in nested format
        nested_event = {
            "data": {
                "hook_event_name": "Notification",
                "session_id": "test-session",
                "cwd": "/test",
                "message": "Claude needs your permission to use Bash",
            }
        }

        stream = io.StringIO(json.dumps(nested_event))
        event = load_hook_event(stream)

        # Verify notification field is a string
        assert event.notification == "Claude needs your permission to use Bash"
        assert isinstance(event.notification, str)
