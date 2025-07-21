"""Global configuration utilities"""

import os
from pathlib import Path


def is_test_environment() -> bool:
    """Check if running in test environment"""
    return os.environ.get("TEST_ENVIRONMENT", "").lower() in ("1", "true", "yes")


def get_cchh_home() -> Path:
    """Get CCHH home directory"""
    home = Path.home() / ".cchh"
    home.mkdir(parents=True, exist_ok=True)
    return home


def get_session_id_from_env() -> str:
    """Get session ID from environment or generate default"""
    return os.environ.get("CLAUDE_SESSION_ID", "default")
