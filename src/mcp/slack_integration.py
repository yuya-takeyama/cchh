"""Slack integration for MCP approval requests."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# Set up logging
log_dir = Path.home() / ".cchh" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"mcp_slack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_debug(message: str):
    """Write debug log to file."""
    with open(log_file, "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"[{timestamp}] {message}\n")
        f.flush()


class SlackIntegration:
    """Send approval requests and results to Slack threads."""

    def __init__(self):
        self.bot_token = os.environ.get("CCHH_SLACK_BOT_TOKEN")
        self.channel_id = os.environ.get("CCHH_SLACK_CHANNEL_ID")
        self.thread_dir = Path.home() / ".cchh" / "slack_threads"
        self.base_url = "http://localhost:8080"

    @property
    def is_configured(self) -> bool:
        """Check if Slack is properly configured."""
        return self.bot_token is not None and self.channel_id is not None

    def get_thread_ts(self, session_id: str) -> Optional[str]:
        """Get Slack thread timestamp for session."""
        thread_file = self.thread_dir / f"{session_id}.json"
        if thread_file.exists():
            try:
                data = json.loads(thread_file.read_text())
                return data.get("thread_ts")
            except Exception:
                return None
        return None

    def send_approval_request(
        self,
        session_id: str,
        request_id: str,
        tool_name: str,
        input_data: dict,
    ) -> bool:
        """Send approval request to Slack thread."""
        log_debug(f"send_approval_request called")
        log_debug(f"session_id: {session_id}")
        log_debug(f"is_configured: {self.is_configured}")
        
        if not self.is_configured:
            log_debug(f"Not configured - bot_token: {bool(self.bot_token)}, channel_id: {bool(self.channel_id)}")
            return False

        thread_ts = self.get_thread_ts(session_id)
        log_debug(f"thread_ts: {thread_ts}")
        log_debug(f"thread_file: {self.thread_dir / f'{session_id}.json'}")
        
        if not thread_ts:
            # No thread found for this session
            log_debug(f"No thread found for session {session_id}")
            return False

        # Build curl commands
        approve_cmd = (
            f'curl -X POST {self.base_url}/approve '
            f'-H "Content-Type: application/json" '
            f'-d \'{{"request_id": "{request_id}"}}\''
        )
        
        deny_cmd = (
            f'curl -X POST {self.base_url}/deny '
            f'-H "Content-Type: application/json" '
            f'-d \'{{"request_id": "{request_id}"}}\''
        )

        # Format input for display
        input_str = json.dumps(input_data, indent=2)
        if len(input_str) > 500:
            input_str = input_str[:500] + "..."

        # Build message
        message = (
            f"🔔 承認要求が来ています\n\n"
            f"*ツール:* `{tool_name}`\n"
            f"*リクエストID:* `{request_id}`\n"
            f"*入力:*\n```{input_str}```\n\n"
            f"承認:\n```{approve_cmd}```\n\n"
            f"却下:\n```{deny_cmd}```"
        )

        return self._send_message(message, thread_ts)

    def send_approval_result(
        self,
        session_id: str,
        request_id: str,
        result: str,  # "approved" or "denied"
    ) -> bool:
        """Send approval result to Slack thread."""
        if not self.is_configured:
            return False

        thread_ts = self.get_thread_ts(session_id)
        if not thread_ts:
            return False

        emoji = "✅" if result == "approved" else "❌"
        status = "承認されました" if result == "approved" else "却下されました"

        message = f"{emoji} リクエスト `{request_id}` が{status}"

        return self._send_message(message, thread_ts)

    def _send_message(self, text: str, thread_ts: str) -> bool:
        """Send message to Slack thread."""
        try:
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": self.channel_id,
                    "text": text,
                    "thread_ts": thread_ts,
                    "mrkdwn": True,
                },
            )
            
            log_debug(f"Slack API response: status={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                log_debug(f"Slack API response data: {json.dumps(data)}")
                return data.get("ok", False)
            else:
                log_debug(f"Slack API error response: {response.text}")
            return False
            
        except Exception as e:
            log_debug(f"Failed to send Slack message: {e}")
            return False