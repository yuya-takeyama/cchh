"""Prompt formatting for Zunda voice synthesis"""

import re


class PromptFormatter:
    """Formats user prompts for voice synthesis"""

    def format(self, prompt: str) -> str:
        """Format prompt for voice synthesis

        Simplifies technical content to be more speakable.
        """
        if not prompt:
            return "空のプロンプトなのだ"

        # 改行を適切に処理
        prompt = prompt.replace("\\n", " ")
        prompt = prompt.replace("\n", " ")

        # 複数スペースを単一スペースに
        prompt = re.sub(r"\s+", " ", prompt).strip()

        # 長すぎるプロンプトは要約
        if len(prompt) > 100:
            # 最初の部分を抽出
            truncated = prompt[:80]
            # 単語の途中で切れないように調整
            if " " in truncated:
                truncated = truncated.rsplit(" ", 1)[0]
            return f"{truncated}、という指示なのだ"

        # 特定のパターンを読みやすく変換
        replacements = {
            # プログラミング用語
            "TODO": "トゥードゥー",
            "FIXME": "フィックスミー",
            "TODO:": "トゥードゥー、",
            "FIXME:": "フィックスミー、",
            "README": "リードミー",
            "API": "エーピーアイ",
            "URL": "ユーアールエル",
            "JSON": "ジェイソン",
            "XML": "エックスエムエル",
            "HTML": "エイチティーエムエル",
            "CSS": "シーエスエス",
            "JS": "ジェイエス",
            "TS": "ティーエス",
            "HTTP": "エイチティーティーピー",
            "HTTPS": "エイチティーティーピーエス",
            # 記号
            "->": "矢印",
            "=>": "矢印",
            "...": "てんてんてん",
            # その他
            "@": "アット",
            "#": "シャープ",
            "&": "アンド",
        }

        formatted = prompt
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)

        # コードブロックやマークダウンを簡略化
        formatted = re.sub(r"```[a-z]*", "コードブロック開始", formatted)
        formatted = formatted.replace("```", "コードブロック終了")
        formatted = re.sub(
            r"`([^`]+)`", r"\1", formatted
        )  # インラインコードの記号を除去

        # URLを簡略化
        formatted = re.sub(r"https?://[^\s]+", "URL", formatted)

        # ファイルパスを読みやすく
        formatted = re.sub(r"[/\\]([^/\\]+\.[a-z]+)", r"、\1ファイル", formatted)

        # 最後に「なのだ」を追加（既に付いていない場合）
        if not formatted.endswith("のだ") and not formatted.endswith("なのだ"):
            formatted += "、という指示なのだ"

        return formatted
