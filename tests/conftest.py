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
    original = os.environ.get("CCHH_TEST_ENVIRONMENT")
    os.environ["CCHH_TEST_ENVIRONMENT"] = "true"
    yield
    if original is None:
        os.environ.pop("CCHH_TEST_ENVIRONMENT", None)
    else:
        os.environ["CCHH_TEST_ENVIRONMENT"] = original


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
def mock_zunda_config(monkeypatch):
    """Mock Zunda configuration"""
    monkeypatch.setenv("CCHH_ZUNDA_SPEAKER_ENABLED", "true")


@pytest.fixture
def disable_all_features(monkeypatch):
    """Disable all notification features"""
    monkeypatch.setenv("CCHH_ZUNDA_SPEAKER_ENABLED", "false")
    monkeypatch.setenv("CCHH_EVENT_LOGGING_ENABLED", "false")
