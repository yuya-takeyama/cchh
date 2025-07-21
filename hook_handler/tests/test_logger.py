"""Tests for logger module"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from hook_handler.logger import ErrorLogger


def test_log_error_basic():
    """Test basic error logging"""
    # Temporarily disable test environment to allow actual logging
    with patch.dict(os.environ, {"TEST_ENVIRONMENT": ""}, clear=False):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            log_file = Path(f.name)

        try:
            logger = ErrorLogger(log_file)
            logger.log_error(
                error_type="test_error",
                error_message="This is a test error",
                context={"test_key": "test_value"},
            )

            # Verify the log file contains the error
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 1

                # Parse the JSON log entry
                entry = json.loads(lines[0])
                assert entry["error_type"] == "test_error"
                assert entry["error_message"] == "This is a test error"
                assert entry["context"]["test_key"] == "test_value"
                assert "timestamp" in entry
                assert entry["timestamp"].endswith("Z")

        finally:
            log_file.unlink()


def test_log_error_with_exception():
    """Test error logging with exception details"""
    # Temporarily disable test environment to allow actual logging
    with patch.dict(os.environ, {"TEST_ENVIRONMENT": ""}, clear=False):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            log_file = Path(f.name)

        try:
            logger = ErrorLogger(log_file)

            # Create a test exception
            try:
                raise ValueError("Test exception")
            except ValueError as e:
                logger.log_error(
                    error_type="test_error",
                    error_message="Error with exception",
                    exception=e,
                )

            # Verify the log file contains the exception details
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 1

                entry = json.loads(lines[0])
                assert "exception" in entry
                assert entry["exception"]["type"] == "ValueError"
                assert entry["exception"]["message"] == "Test exception"
                assert "traceback" in entry["exception"]
                assert "ValueError: Test exception" in entry["exception"]["traceback"]

        finally:
            log_file.unlink()


def test_log_error_multiple_entries():
    """Test logging multiple errors creates JSONL format"""
    # Temporarily disable test environment to allow actual logging
    with patch.dict(os.environ, {"TEST_ENVIRONMENT": ""}, clear=False):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            log_file = Path(f.name)

        try:
            logger = ErrorLogger(log_file)

            # Log multiple errors
            for i in range(3):
                logger.log_error(
                    error_type=f"error_{i}",
                    error_message=f"Error message {i}",
                )

            # Verify JSONL format (one JSON per line)
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 3

                for i, line in enumerate(lines):
                    # Each line should be valid JSON
                    entry = json.loads(line)
                    assert entry["error_type"] == f"error_{i}"
                    assert entry["error_message"] == f"Error message {i}"

        finally:
            log_file.unlink()


def test_log_error_handles_write_failure():
    """Test error logging handles write failures gracefully"""
    # Temporarily disable test environment to allow actual logging
    with patch.dict(os.environ, {"TEST_ENVIRONMENT": ""}, clear=False):
        # Use a directory path as log file (will fail to write)
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir)

            logger = ErrorLogger(log_file)

            # This should not raise an exception
            with patch("logging.Logger.error") as mock_logger_error:
                logger.log_error(
                    error_type="test_error",
                    error_message="This should fail",
                )

                # Verify standard logger was called
                mock_logger_error.assert_called_once()
                assert (
                    "Failed to write error log entry"
                    in mock_logger_error.call_args[0][0]
                )


def test_log_error_creates_directory():
    """Test that ErrorLogger creates the log directory if it doesn't exist"""
    # Temporarily disable test environment to allow actual logging
    with patch.dict(os.environ, {"TEST_ENVIRONMENT": ""}, clear=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path to a non-existent subdirectory
            log_file = Path(tmpdir) / "subdir" / "error.log"

            # Directory shouldn't exist yet
            assert not log_file.parent.exists()

            logger = ErrorLogger(log_file)

            # Directory should now exist
            assert log_file.parent.exists()

            # Should be able to write to the log
            logger.log_error(
                error_type="test_error",
                error_message="Test message",
            )

            assert log_file.exists()

            # Verify content
            with open(log_file) as f:
                entry = json.loads(f.read())
                assert entry["error_type"] == "test_error"
