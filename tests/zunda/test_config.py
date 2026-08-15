"""Test cases for Zunda configuration"""

import os
from unittest.mock import patch

from src.zunda.config import ZundaConfig


class TestZundaConfig:
    """Test cases for ZundaConfig"""

    def test_speak_commands_disabled_by_default(self):
        """Test that command speech is disabled unless explicitly enabled"""
        with patch.dict(os.environ, {}, clear=True):
            assert ZundaConfig().speak_commands is False

    def test_speak_commands_can_be_enabled(self):
        """Test that command speech can be enabled via environment variable"""
        for value in ("1", "true", "yes", "TRUE"):
            with patch.dict(
                os.environ, {"CCHH_ZUNDA_SPEAK_COMMANDS_ENABLED": value}, clear=True
            ):
                assert ZundaConfig().speak_commands is True

    def test_speak_commands_explicitly_disabled(self):
        """Test that an explicit false value keeps command speech disabled"""
        with patch.dict(
            os.environ, {"CCHH_ZUNDA_SPEAK_COMMANDS_ENABLED": "false"}, clear=True
        ):
            assert ZundaConfig().speak_commands is False
