"""Command formatting for Zunda voice synthesis"""

from ..utils.command_parser import parse_bash_command


class CommandFormatter:
    """Formats commands for voice synthesis (simplified)"""

    def __init__(self):
        # Rule 1: Word to pronunciation mapping (minimal set)
        self.words: dict[str, str] = {
            "npm": "エヌピーエム",
            "pnpm": "ピーエヌピーエム",
            "tsx": "ティーエスエックス",
        }

        # Rule 2: How many parts to read for each command pattern
        self.parts_limit: dict[str, int] = {
            # Git - command + subcommand
            "git": 2,
            # Package managers
            "npm": 2,
            "npm run": 3,  # npm run <script>
            "yarn": 2,
            "yarn run": 3,
            "pnpm": 2,
            "pnpm run": 3,
            # UV special cases
            "uv": 2,
            "uv run": 3,  # uv run <command>
            "uv run task": 4,  # uv run task <name>
            # Docker
            "docker": 2,
            "docker compose": 3,
            # GitHub CLI
            "gh": 2,
            "gh pr": 3,
            "gh issue": 3,
            # Other tools
            "go": 2,
            "go mod": 3,
            "cargo": 2,
            "kubectl": 2,
            "terraform": 2,
        }

    def format(self, command: str) -> str:
        """Format command for voice synthesis

        Returns a very simplified, speakable version of the command.
        """
        # Parse command
        parsed = parse_bash_command(command)
        parts = [parsed["command"]] + (
            parsed["args"] if isinstance(parsed["args"], list) else []
        )

        if not parts:
            return ""

        # Rule 1: Exact command match
        if command in self.words:
            return self.words[command]

        # Rule 2: Determine how many parts to read
        limit = self._get_parts_limit(parts)

        # Rule 3: Convert each part using word dictionary
        result = []
        for part in parts[:limit]:
            result.append(self.words.get(part, part))

        return " ".join(result)

    def _get_parts_limit(self, parts: list[str]) -> int:
        """Determine how many parts to read"""
        # Check explicit limits (longest match first)
        for length in range(min(4, len(parts)), 0, -1):
            key = " ".join(parts[:length])
            if key in self.parts_limit:
                return self.parts_limit[key]

        # Check single command patterns
        if parts and parts[0] in self.parts_limit:
            return self.parts_limit[parts[0]]

        # Default: just the command
        return 1
