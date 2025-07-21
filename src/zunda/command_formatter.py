"""Command formatting for Zunda voice synthesis"""

from ..utils.command_parser import parse_bash_command


class CommandFormatter:
    """Formats commands for voice synthesis (simplified)"""

    def __init__(self):
        # コマンド名の日本語読み上げマップ
        self.command_map = {
            "python": "パイソン",
            "python3": "パイソン",
            "npm": "エヌピーエム",
            "pnpm": "ピーエヌピーエム",
            "yarn": "ヤーン",
            "git": "ギット",
            "docker": "ドッカー",
            "kubectl": "キューブコントロール",
            "terraform": "テラフォーム",
            "make": "メイク",
            "cargo": "カーゴ",
            "rustc": "ラストシー",
            "go": "ゴー",
            "node": "ノード",
            "deno": "ディーノ",
            "bun": "バン",
            "curl": "カール",
            "wget": "ダブルゲット",
            "ssh": "エスエスエイチ",
            "scp": "エスシーピー",
            "rsync": "アールシンク",
            "grep": "グレップ",
            "find": "ファインド",
            "sed": "セド",
            "awk": "オーク",
            "chmod": "チーエムオーディー",
            "chown": "チーオウン",
            "sudo": "スードゥー",
            "apt": "エーピーティー",
            "brew": "ブリュー",
            "pip": "ピップ",
            "poetry": "ポエトリー",
            "uv": "ユーブイ",
            "ruff": "ラフ",
            "pytest": "パイテスト",
            "mypy": "マイパイ",
            "black": "ブラック",
            "eslint": "イーエスリント",
            "prettier": "プリティア",
            "jest": "ジェスト",
            "vitest": "ヴィテスト",
            "vite": "ヴィート",
            "webpack": "ウェブパック",
            "parcel": "パーセル",
            "rollup": "ロールアップ",
            "tsc": "ティーエスシー",
            "tsx": "ティーエスエックス",
            "ts-node": "ティーエスノード",
        }

    def format(self, command: str) -> str:
        """Format command for voice synthesis

        Returns a very simplified, speakable version of the command.
        """
        # 基本的なコマンド解析
        parsed = parse_bash_command(command)
        cmd_name = parsed["command"]
        args: list[str] = parsed["args"] if isinstance(parsed["args"], list) else []

        # コマンド名を日本語に変換
        readable_name = self.command_map.get(cmd_name, cmd_name)

        # 特定のパターンに対する特別な処理
        if cmd_name == "git":
            if args and args[0] in [
                "add",
                "commit",
                "push",
                "pull",
                "clone",
                "checkout",
                "branch",
                "merge",
            ]:
                git_action_map = {
                    "add": "アド",
                    "commit": "コミット",
                    "push": "プッシュ",
                    "pull": "プル",
                    "clone": "クローン",
                    "checkout": "チェックアウト",
                    "branch": "ブランチ",
                    "merge": "マージ",
                }
                action = git_action_map.get(args[0], args[0])
                return f"ギット{action}"

        elif cmd_name in ["npm", "yarn", "pnpm"]:
            if args and args[0] in [
                "install",
                "run",
                "start",
                "test",
                "build",
            ]:
                action_map = {
                    "install": "インストール",
                    "run": "ラン",
                    "start": "スタート",
                    "test": "テスト",
                    "build": "ビルド",
                }
                action = action_map.get(args[0], args[0])
                return f"{readable_name}で{action}"

        elif cmd_name == "cd":
            return "ディレクトリ移動"

        elif cmd_name in ["ls", "dir"]:
            return "ファイル一覧表示"

        elif cmd_name in ["cat", "less", "more", "head", "tail"]:
            return "ファイル内容表示"

        elif cmd_name in ["vi", "vim", "nvim", "nano", "emacs"]:
            return "エディタ起動"

        elif cmd_name == "echo":
            return "文字列出力"

        elif cmd_name == "mkdir":
            return "ディレクトリ作成"

        elif cmd_name == "touch":
            return "ファイル作成"

        elif cmd_name in ["rm", "rmdir"]:
            return "削除コマンド"

        elif cmd_name in ["cp", "mv"]:
            return "ファイル操作"

        # デフォルト：コマンド名のみ
        return f"{readable_name}"
