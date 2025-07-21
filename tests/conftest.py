"""Pytest configuration and shared fixtures"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def test_environment():
    """Automatically set TEST_ENVIRONMENT for all tests"""
    original = os.environ.get("TEST_ENVIRONMENT")
    os.environ["TEST_ENVIRONMENT"] = "true"
    yield
    if original is None:
        os.environ.pop("TEST_ENVIRONMENT", None)
    else:
        os.environ["TEST_ENVIRONMENT"] = original


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    original = os.environ.get("CCHH_LOG_DIR")
    os.environ["CCHH_LOG_DIR"] = str(log_dir)
    yield log_dir
    if original is None:
        os.environ.pop("CCHH_LOG_DIR", None)
    else:
        os.environ["CCHH_LOG_DIR"] = original


@pytest.fixture
def mock_slack_config(monkeypatch):
    """Mock Slack configuration"""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C1234567890")
    monkeypatch.setenv("SLACK_NOTIFICATIONS_ENABLED", "true")


@pytest.fixture
def mock_zunda_config(monkeypatch):
    """Mock Zunda configuration"""
    monkeypatch.setenv("ZUNDA_SPEAKER_ENABLED", "true")
    monkeypatch.setenv("ZUNDA_SPEAK_SPEED", "1.2")


@pytest.fixture
def disable_all_features(monkeypatch):
    """Disable all notification features"""
    monkeypatch.setenv("SLACK_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("ZUNDA_SPEAKER_ENABLED", "false")
    monkeypatch.setenv("EVENT_LOGGING_ENABLED", "false")
