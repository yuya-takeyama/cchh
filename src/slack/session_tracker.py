"""Session tracking for Slack notifications

Tracks Claude Code sessions to determine when to show cwd in Slack.
"""

import os
import time
from pathlib import Path
from typing import Optional, Set


class SlackSessionTracker:
    """Tracks Claude Code sessions for Slack notifications

    Determines if this is a new session to display cwd in Slack channel.
    """

    def __init__(self, session_id: str, session_dir: Optional[Path] = None):
        self.session_id = session_id
        self.session_dir = session_dir or Path.home() / ".cchh" / "sessions"
        self.session_file = self.session_dir / f"{session_id}.session"
        self.is_new_session = self._check_new_session()

    def _check_new_session(self) -> bool:
        """Check if this is a new session"""
        # セッションディレクトリが存在しない場合は作成
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # セッションファイルが存在しない場合は新規セッション
        if not self.session_file.exists():
            self._create_session_file()
            return True

        # セッションファイルの更新時刻をチェック
        # 24時間以上古い場合は新規セッションとみなす
        mtime = self.session_file.stat().st_mtime
        if time.time() - mtime > 86400:  # 24 hours
            self._create_session_file()
            return True

        # 既存セッションを更新
        self.session_file.touch()
        return False

    def _create_session_file(self) -> None:
        """Create or update session file"""
        self.session_file.write_text(str(time.time()))

    def get_active_sessions(self) -> Set[str]:
        """Get all active session IDs"""
        active_sessions = set()

        if not self.session_dir.exists():
            return active_sessions

        current_time = time.time()
        for session_file in self.session_dir.glob("*.session"):
            try:
                mtime = session_file.stat().st_mtime
                # 24時間以内のセッションをアクティブとみなす
                if current_time - mtime < 86400:
                    session_id = session_file.stem
                    active_sessions.add(session_id)
            except (OSError, ValueError):
                continue

        return active_sessions

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Clean up session files older than specified days"""
        if not self.session_dir.exists():
            return 0

        current_time = time.time()
        cutoff_time = days * 86400
        removed_count = 0

        for session_file in self.session_dir.glob("*.session"):
            try:
                mtime = session_file.stat().st_mtime
                if current_time - mtime > cutoff_time:
                    session_file.unlink()
                    removed_count += 1
            except OSError:
                continue

        return removed_count
