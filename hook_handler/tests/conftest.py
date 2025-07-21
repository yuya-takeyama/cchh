"""Pytest configuration and fixtures"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ["TEST_ENVIRONMENT"] = "1"
    yield
    # Cleanup (remove the env var after tests)
    os.environ.pop("TEST_ENVIRONMENT", None)
