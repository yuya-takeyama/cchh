"""Test cases for event logger"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.types import HookEvent
from src.logger.event_logger import EventLogger


@pytest.fixture
def event_logger(temp_log_dir):
    """Create EventLogger instance with temp directory"""
    with patch("src.logger.event_logger.is_test_environment", return_value=False):
        logger = EventLogger(log_file=temp_log_dir / "test.jsonl")
        yield logger


@pytest.fixture
def sample_event():
    """Create a sample hook event"""
    return HookEvent(
        hook_event_name="PreToolUse",
        session_id="test-session-123",
        cwd="/test/directory",
        tool_name="Bash",
        tool_input={"command": "echo test"},
    )


class TestEventLogger:
    """Test cases for EventLogger"""

    def test_logger_disabled(self, sample_event, monkeypatch, temp_log_dir):
        """Test that disabled logger doesn't write files"""
        monkeypatch.setenv("CCHH_EVENT_LOGGING_ENABLED", "false")
        logger = EventLogger(log_file=temp_log_dir / "test.jsonl")
        logger.handle_event(sample_event)

        # No log files should be created
        log_files = list(temp_log_dir.glob("*.jsonl"))
        assert len(log_files) == 0

    def test_log_event_creation(self, event_logger, sample_event, temp_log_dir):
        """Test that events are logged to file"""
        event_logger.handle_event(sample_event)

        # Check log file was created
        log_files = list(temp_log_dir.glob("*.jsonl"))
        assert len(log_files) == 1

        # Check content
        with open(log_files[0]) as f:
            log_entry = json.loads(f.readline())

        assert log_entry["raw_input"]["hook_event_name"] == "PreToolUse"
        assert log_entry["raw_input"]["session_id"] == "test-session-123"
        assert log_entry["raw_input"]["tool_name"] == "Bash"
        assert "time" in log_entry

    def test_multiple_events_same_file(self, event_logger, sample_event, temp_log_dir):
        """Test multiple events are appended to same file"""
        # Log multiple events
        for i in range(5):
            event = sample_event
            event.tool_input = {"command": f"echo test{i}"}
            event_logger.handle_event(event)

        # Should have one file
        log_files = list(temp_log_dir.glob("*.jsonl"))
        assert len(log_files) == 1

        # Should have 5 lines
        with open(log_files[0]) as f:
            lines = f.readlines()
        assert len(lines) == 5

        # Check each line is valid JSON
        for i, line in enumerate(lines):
            entry = json.loads(line)
            assert f"test{i}" in entry["raw_input"]["tool_input"]["command"]

    @pytest.mark.skip(reason="Log rotation test needs fixing")
    def test_log_rotation(self, event_logger, sample_event, temp_log_dir, monkeypatch):
        """Test log rotation when file gets too large"""
        # Set a very small max log size for testing
        with patch("src.logger.config.logger_config.max_log_size", 1000):  # 1KB
            # Mock a large existing log file
            log_file = event_logger.log_file

            # Write a large amount of data to simulate large file
            with open(log_file, "w") as f:
                for _ in range(100):
                    f.write(json.dumps({"test": "data" * 50}) + "\n")

            # Log a new event (should trigger rotation)
            event_logger.handle_event(sample_event)

            # Should have 2 files now (original rotated + new)
            # Check in the log file's directory, not temp_log_dir
            log_files = list(log_file.parent.glob("*.jsonl*"))
            assert len(log_files) >= 2

    def test_different_event_types(self, event_logger, temp_log_dir):
        """Test logging different event types"""
        events = [
            HookEvent(
                hook_event_name="UserPromptSubmit",
                session_id="test-session",
                cwd="/test",
                prompt="Test prompt",
            ),
            HookEvent(
                hook_event_name="Stop",
                session_id="test-session",
                cwd="/test",
            ),
            HookEvent(
                hook_event_name="Notification",
                session_id="test-session",
                cwd="/test",
                notification="Test notification",
            ),
        ]

        for event in events:
            event_logger.handle_event(event)

        # Check all events were logged
        log_files = list(temp_log_dir.glob("*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0]) as f:
            lines = f.readlines()
        assert len(lines) == 3

        # Verify event types
        logged_types = [
            json.loads(line)["raw_input"]["hook_event_name"] for line in lines
        ]
        assert "UserPromptSubmit" in logged_types
        assert "Stop" in logged_types
        assert "Notification" in logged_types

    def test_handle_event_with_error(self, event_logger, sample_event, monkeypatch):
        """Test that logging errors don't crash the handler"""
        # Make log file path invalid to cause error
        monkeypatch.setattr(event_logger, "log_file", Path("/invalid/path/test.jsonl"))

        # Should not raise exception
        event_logger.handle_event(sample_event)

    def test_timestamp_format(self, event_logger, sample_event, temp_log_dir):
        """Test that timestamps are properly formatted"""
        event_logger.handle_event(sample_event)

        log_files = list(temp_log_dir.glob("*.jsonl"))
        with open(log_files[0]) as f:
            log_entry = json.loads(f.readline())

        # Check timestamp is ISO format
        timestamp = log_entry["time"]
        parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed_time, datetime)

    def test_preserve_all_event_fields(self, event_logger, temp_log_dir):
        """Test that all event fields are preserved in log"""
        event = HookEvent(
            hook_event_name="PostToolUse",
            session_id="test-session",
            cwd="/test/dir",
            tool_name="Edit",
            tool_input={
                "file_path": "/test/file.py",
                "old_string": "old",
                "new_string": "new",
            },
            result={"success": True, "lines_changed": 5},
        )

        event_logger.handle_event(event)

        log_files = list(temp_log_dir.glob("*.jsonl"))
        with open(log_files[0]) as f:
            log_entry = json.loads(f.readline())

        # Check all fields are present
        assert log_entry["raw_input"]["hook_event_name"] == "PostToolUse"
        assert log_entry["raw_input"]["session_id"] == "test-session"
        assert log_entry["raw_input"]["cwd"] == "/test/dir"
        assert log_entry["raw_input"]["tool_name"] == "Edit"
        assert log_entry["raw_input"]["tool_input"]["file_path"] == "/test/file.py"
        assert log_entry["raw_input"]["result"]["success"] is True

    def test_concurrent_logging(self, event_logger, sample_event, temp_log_dir):
        """Test that concurrent events are handled properly"""
        import threading

        def log_events():
            for i in range(10):
                event = HookEvent(
                    hook_event_name="PreToolUse",
                    session_id=f"session-{threading.current_thread().name}",
                    cwd="/test",
                    tool_name="Bash",
                    tool_input={"command": f"echo {i}"},
                )
                event_logger.handle_event(event)

        # Run multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=log_events, name=f"thread-{i}")
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have logged all events
        log_files = list(temp_log_dir.glob("*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0]) as f:
            lines = f.readlines()
        assert len(lines) == 30  # 3 threads * 10 events each
