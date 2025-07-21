"""Test cases for session management"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hook_handler.session import SessionManager


@pytest.fixture
def session_manager():
    """Create SessionManager instance with temporary directory"""
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    test_session_id = "test-session-123"

    # Patch settings to use temp directory
    with patch("hook_handler.session.settings") as mock_settings:
        mock_settings.thread_dir = Path(temp_dir) / "thread_states"
        mock_settings.thread_dir.mkdir(parents=True, exist_ok=True)

        session_manager = SessionManager(test_session_id)
        session_manager.temp_dir = temp_dir  # Store for cleanup
        yield session_manager

    # Clean up temp directory
    shutil.rmtree(temp_dir)


def test_new_session(session_manager):
    """Test new session detection"""
    assert session_manager.is_new_session is True
    assert session_manager.thread_ts is None


def test_save_and_load_state(session_manager):
    """Test saving and loading session state"""
    test_thread_ts = "ts-123456789"

    # Save state
    result = session_manager.save_state(test_thread_ts)
    assert result is True

    # Load state
    state = session_manager.load_state()
    assert state is not None
    assert state["thread_ts"] == test_thread_ts
    assert state["session_id"] == "test-session-123"
    assert "created_at" in state

    # Check properties
    assert session_manager.thread_ts == test_thread_ts
    assert session_manager.is_new_session is False


def test_load_nonexistent_state(session_manager):
    """Test loading state when file doesn't exist"""
    state = session_manager.load_state()
    assert state is None


def test_load_corrupted_state(session_manager):
    """Test loading corrupted state file"""
    # Create corrupted file
    state_file = session_manager._state_file
    with open(state_file, "w") as f:
        f.write("not valid json")

    # Should return None on error
    state = session_manager.load_state()
    assert state is None


def test_save_state_io_error(session_manager):
    """Test save state with IO error"""
    import os

    # Make directory read-only
    os.chmod(session_manager._state_file.parent, 0o444)

    # Should return False on error
    result = session_manager.save_state("test-ts")
    assert result is False

    # Restore permissions
    os.chmod(session_manager._state_file.parent, 0o755)
