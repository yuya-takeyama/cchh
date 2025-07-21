"""Ultra-simple command converter for readable speech synthesis"""

import shlex


class SimpleCommandConverter:
    """Ultra-simple command converter with just 2 rule types"""

    def __init__(self):
        # Rule 1: Simple word dictionary
        self.words: dict[str, str] = {
            # Exact commands
            "pwd": "ピーダブルディー",
            # Programs
            "git": "ギット",
            "npm": "エヌピーエム",
            "pnpm": "ピーエヌピーエム",
            "uv": "ユーブイ",
            "gh": "gh",
            "ls": "エルエス",
            "rm": "アールエム",
            "cp": "シーピー",
            "mv": "エムブイ",
            "cat": "キャット",
            "echo": "エコー",
            "mkdir": "エムケーディーアイアール",
            "touch": "タッチ",
            "cd": "シーディー",
            "python3": "パイソンスリー",
            "tsx": "ティーエスエックス",
            "npx": "エヌピーエックス",
            "yarn": "yarn",
            "docker": "docker",
            "go": "go",
            # Subcommands
            "status": "ステータス",
            "commit": "コミット",
            "push": "プッシュ",
            "pull": "プル",
            "fetch": "フェッチ",
            "add": "アッド",
            "install": "インストール",
            "run": "ラン",
            "test": "テスト",
            "build": "ビルド",
            "sync": "シンク",
            "format": "フォーマット",
            "task": "タスク",
            "pr": "pr",
            "issue": "issue",
            "create": "create",
            "list": "list",
        }

        # Rule 2: How many parts to read (space-separated keys)
        self.parts_limit: dict[str, int] = {
            "docker": 2,
            "gh issue": 3,
            "gh pr": 3,
            "git": 2,
            "go": 2,
            "go mod": 3,
            "npm": 2,
            "pnpm": 2,
            "uv": 2,
            "uv run task": 4,
            "yarn": 2,
        }

    def convert(self, command: str) -> str:
        """Convert command to readable format"""
        if not command:
            return command

        command = command.strip()

        # Special case: exact match
        if command in self.words:
            return self.words[command]

        # Parse command
        parts = self._parse_command(command)
        if not parts:
            return command

        # Determine how many parts to read
        limit = self._get_parts_limit(parts)

        # Convert each part
        result = []
        for part in parts[:limit]:
            result.append(self.words.get(part, part))

        return " ".join(result)

    def _parse_command(self, command: str) -> list[str]:
        """Parse command into parts"""
        try:
            return shlex.split(command)
        except ValueError:
            return command.split()

    def _get_parts_limit(self, parts: list[str]) -> int:
        """Determine how many parts to read"""
        # Check explicit limits (longest match first)
        for length in range(min(3, len(parts)), 0, -1):
            key = " ".join(parts[:length])
            if key in self.parts_limit:
                return self.parts_limit[key]

        # Check single command patterns
        if parts and parts[0] in self.parts_limit:
            return self.parts_limit[parts[0]]

        # Default: just the command
        return 1
