"""Session and thread state management"""

import json
from datetime import datetime
from typing import Any

from .config import settings


class SessionManager:
    """Manage session and thread state"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._state_file = settings.thread_dir / f"{session_id}.json"

    def load_state(self) -> dict[str, Any] | None:
        """セッションのスレッド状態を読み込み"""
        if not self._state_file.exists():
            return None

        try:
            with open(self._state_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def save_state(self, thread_ts: str) -> bool:
        """セッションのスレッド状態を保存"""
        state = {
            "thread_ts": thread_ts,
            "created_at": datetime.now().isoformat(),
            "session_id": self.session_id,
        }

        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    @property
    def thread_ts(self) -> str | None:
        """Get current thread timestamp"""
        state = self.load_state()
        return state.get("thread_ts") if state else None

    @property
    def is_new_session(self) -> bool:
        """Check if this is a new session"""
        return self.load_state() is None
