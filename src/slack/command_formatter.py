"""Command formatting for Slack notifications"""

from .config import slack_config


class CommandFormatter:
    """Formats commands for Slack display with appropriate truncation"""

    def __init__(self, max_length: int | None = None):
        self.max_length = max_length or slack_config.command_max_length

    def format(self, command: str) -> str:
        """Format command for Slack display

        Long commands are truncated with <snip> to show where content was removed.
        """
        if len(command) <= self.max_length:
            return command

        # コマンド名と最初の引数を抽出
        parts = command.split(maxsplit=1)
        if len(parts) == 1:
            # 引数なしのコマンドでも長い場合は単純に切り詰め
            return command[: self.max_length - 8] + " <snip>"

        cmd_name, args = parts

        # パイプラインやリダイレクトを含む場合は特別処理
        if "|" in command or ">" in command or "<" in command:
            # 最初の部分と最後の部分を残す
            if len(command) > self.max_length:
                keep_start = self.max_length // 2 - 10
                keep_end = self.max_length // 2 - 10
                return f"{command[:keep_start]} <snip> {command[-keep_end:]}"

        # コマンド名 + 最初の引数が既に長い場合
        if (
            len(cmd_name) + len(args.split()[0] if args else "") + 1
            > self.max_length - 8
        ):
            return f"{cmd_name} <snip>"

        # 引数部分を適切に切り詰め
        available_space = self.max_length - len(cmd_name) - 8  # " <snip>" の分
        truncated_args = args[:available_space]

        # 単語の途中で切れないように調整
        if " " in truncated_args:
            truncated_args = truncated_args.rsplit(" ", 1)[0]

        return f"{cmd_name} {truncated_args} <snip>"

    def format_with_context(self, command: str, description: str | None = None) -> str:
        """Format command with optional description"""
        formatted_cmd = self.format(command)

        if description:
            return f"{description}: `{formatted_cmd}`"
        return f"`{formatted_cmd}`"
