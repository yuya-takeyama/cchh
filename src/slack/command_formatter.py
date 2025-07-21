"""Command formatting for Slack notifications"""

from .config import slack_config


class CommandFormatter:
    """Formats commands for Slack display with appropriate truncation"""

    def __init__(self, max_length: int | None = None):
        self.max_length = max_length or slack_config.command_max_length

    def format(self, command: str) -> str:
        """Format command for Slack display

        Currently returns the full command without truncation.
        """
        # 一旦<snip>処理を無効化してフルコマンドを返す
        return command

    def format_with_context(self, command: str, description: str | None = None) -> str:
        """Format command with optional description"""
        formatted_cmd = self.format(command)

        if description:
            return f"{description}: `{formatted_cmd}`"
        return f"`{formatted_cmd}`"
