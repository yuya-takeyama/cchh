"""Tests for command converter"""

from hook_handler.command_converter import SimpleCommandConverter


class TestCommandConverter:
    def setup_method(self):
        self.converter = SimpleCommandConverter()

    def test_git_fetch_origin_skip(self):
        """git fetch origin → git fetch shortening"""
        # Now 'fetch' is in SUBCOMMAND_REPLACEMENTS, and we have skip rules
        assert self.converter.convert("git fetch origin") == "ギット フェッチ"
        assert self.converter.convert("git fetch upstream") == "ギット フェッチ"
        assert self.converter.convert("git fetch") == "ギット フェッチ"

    def test_git_push_origin_skip(self):
        """git push origin → git push shortening"""
        assert self.converter.convert("git push origin main") == "ギット プッシュ"
        assert self.converter.convert("git push") == "ギット プッシュ"

    def test_git_pull_origin_skip(self):
        """git pull origin → git pull shortening"""
        assert self.converter.convert("git pull origin") == "ギット プル"
        assert self.converter.convert("git pull") == "ギット プル"

    def test_no_subcommand_pattern(self):
        """Commands without subcommand patterns"""
        # Default behavior - reads only first part if no subcommand pattern
        result = self.converter.convert("terraform plan -out=tfplan")
        assert result == "terraform"  # Not in subcommand list, so only first part

        # Another example
        assert self.converter.convert("wget http://example.com") == "wget"

    def test_exact_match(self):
        """Exact command matching"""
        assert self.converter.convert("pwd") == "ピーダブルディー"

    def test_simple_commands(self):
        """Simple commands (program name only)"""
        assert self.converter.convert("ls -la") == "エルエス"
        assert self.converter.convert("rm -rf /tmp") == "アールエム"
        assert self.converter.convert("cp file1 file2") == "シーピー"
        assert self.converter.convert("mv old new") == "エムブイ"
        assert self.converter.convert("cat /etc/hosts") == "キャット"
        assert self.converter.convert("echo 'hello'") == "エコー"
        assert self.converter.convert("touch file.txt") == "タッチ"
        assert (
            self.converter.convert("mkdir -p /tmp/test") == "エムケーディーアイアール"
        )

    def test_subcommand_programs(self):
        """Programs with subcommands"""
        assert self.converter.convert("git status") == "ギット ステータス"
        assert self.converter.convert("git commit -m") == "ギット コミット"
        assert self.converter.convert("npm install") == "エヌピーエム インストール"
        assert self.converter.convert("npm run test") == "エヌピーエム ラン"
        assert self.converter.convert("pnpm install") == "ピーエヌピーエム インストール"
        assert self.converter.convert("yarn add react") == "yarn アッド"

    def test_uv_special_patterns(self):
        """uv command special patterns"""
        # uv sync (normal pattern)
        assert self.converter.convert("uv sync") == "ユーブイ シンク"

        # uv run task patterns (4 parts)
        assert (
            self.converter.convert("uv run task format")
            == "ユーブイ ラン タスク フォーマット"
        )
        assert (
            self.converter.convert("uv run task test") == "ユーブイ ラン タスク テスト"
        )
        assert (
            self.converter.convert("uv run task build") == "ユーブイ ラン タスク ビルド"
        )

        # uv run patterns (default 2 parts behavior)
        assert self.converter.convert("uv run pytest") == "ユーブイ ラン"
        assert self.converter.convert("uv run ruff check") == "ユーブイ ラン"

        # Other uv commands
        assert self.converter.convert("uv add requests") == "ユーブイ アッド"
        assert self.converter.convert("uv install") == "ユーブイ インストール"

    def test_gh_special_patterns(self):
        """gh command special patterns"""
        assert self.converter.convert("gh pr create") == "gh pr create"
        assert self.converter.convert("gh pr list") == "gh pr list"
        assert self.converter.convert("gh issue create") == "gh issue create"
        assert (
            self.converter.convert("gh repo clone") == "gh"
        )  # 'clone' not in subcommands

    def test_unknown_commands(self):
        """Commands not in replacement lists"""
        assert self.converter.convert("unknown-command") == "unknown-command"
        assert self.converter.convert("custom-script arg1") == "custom-script"

    def test_shlex_failure(self):
        """Handle shlex parsing failures"""
        # Unclosed quote
        result = self.converter.convert("echo 'unclosed")
        assert result == "エコー"

    def test_empty_and_whitespace(self):
        """Handle empty and whitespace-only commands"""
        assert self.converter.convert("") == ""
        assert self.converter.convert("   ") == ""

    def test_parts_limit_rules(self):
        """Test commands with explicit parts limit rules"""
        # git clone is limited to 2 parts
        assert (
            self.converter.convert("git clone https://github.com/repo.git")
            == "ギット clone"
        )

        # docker run is limited to 2 parts
        assert self.converter.convert("docker run -it ubuntu bash") == "docker ラン"

        # npm run is limited to 2 parts
        assert self.converter.convert("npm run test:unit") == "エヌピーエム ラン"

    def test_git_commands_always_two_parts(self):
        """Test that all git commands read 2 parts (command + subcommand)"""
        # Commands not explicitly in parts_limit should still read 2 parts
        assert self.converter.convert("git checkout main") == "ギット checkout"
        assert self.converter.convert("git branch -a") == "ギット branch"
        assert self.converter.convert("git merge feature") == "ギット merge"
        assert self.converter.convert("git rebase origin/main") == "ギット rebase"
        assert self.converter.convert("git log --oneline") == "ギット log"
        assert self.converter.convert("git diff HEAD~1") == "ギット diff"
        assert self.converter.convert("git stash") == "ギット stash"
        assert self.converter.convert("git reset --hard") == "ギット reset"

        # Commands with single part should still work
        assert self.converter.convert("git") == "ギット"

    def test_go_commands(self):
        """Test go commands with special handling for go mod"""
        # Regular go commands (2 parts)
        assert self.converter.convert("go build") == "go ビルド"
        assert self.converter.convert("go test") == "go テスト"
        assert self.converter.convert("go run main.go") == "go ラン"
        assert self.converter.convert("go get github.com/pkg") == "go get"

        # go mod commands (3 parts)
        assert self.converter.convert("go mod tidy") == "go mod tidy"
        assert self.converter.convert("go mod init") == "go mod init"
        assert self.converter.convert("go mod download") == "go mod download"
        assert self.converter.convert("go mod vendor") == "go mod vendor"

        # Single part
        assert self.converter.convert("go") == "go"

    def test_backward_compatibility(self):
        """Ensure backward compatibility with existing behavior"""
        # All existing test cases should pass
        test_cases = [
            ("pwd", "ピーダブルディー"),
            ("git status", "ギット ステータス"),
            ("npm install", "エヌピーエム インストール"),
            ("uv sync", "ユーブイ シンク"),
            ("uv run task format", "ユーブイ ラン タスク フォーマット"),
            ("ls -la", "エルエス"),
            ("rm -rf /tmp", "アールエム"),
            ("echo 'hello world'", "エコー"),
            ("gh pr create --draft", "gh pr create"),
        ]

        for cmd, expected in test_cases:
            assert self.converter.convert(cmd) == expected, f"Failed for: {cmd}"
