"""Zundaspeak configuration"""

import os
from enum import Enum


class ZundaspeakStyle(Enum):
    """Zundaspeakの読み上げスタイル"""

    NORMAL = "0"  # ノーマル
    AMAAMA = "1"  # あまあま
    TSUNTSUN = "2"  # ツンツン
    SEXY = "3"  # セクシー
    SASAYAKI = "4"  # ささやき
    HISOHISO = "5"  # ヒソヒソ
    HEROHERO = "6"  # ヘロヘロ
    NAMIDAME = "7"  # なみだめ


class ZundaConfig:
    """Zunda-specific configuration"""

    def __init__(self):
        # Zunda settings
        self.enabled = self._get_bool_env("CCHH_ZUNDA_SPEAKER_ENABLED", True)
        self.speak_on_prompt_submit = self._get_bool_env(
            "CCHH_ZUNDA_SPEAK_ON_PROMPT_SUBMIT", True
        )
        self.default_style = ZundaspeakStyle.NORMAL

        # Silent commands (commands that should not be spoken)
        self.silent_commands = [
            "git status",
            "git log",
            "git diff",
            "ls",
            "pwd",
            "cat",
        ]

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.environ.get(key, str(default)).lower()
        return value in ("1", "true", "yes")

    def is_silent_command(self, command: str) -> bool:
        """Check if command should be silent"""
        return any(
            command.strip().startswith(silent_cmd)
            for silent_cmd in self.silent_commands
        )


# Global instance
zunda_config = ZundaConfig()
