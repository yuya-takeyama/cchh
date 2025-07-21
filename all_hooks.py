#!/usr/bin/env python3
"""Claude Code All Hooks Handler - 全イベントを処理

This script processes all Claude Code hook events and dispatches them to
appropriate handlers (Slack notifications, Zunda voice, event logging).
"""

import json
import sys

from src.core.dispatcher import EventDispatcher
from src.utils.io_helpers import load_hook_event, write_hook_event
from src.utils.logger import get_debug_logger


def main() -> None:
    """Main entry point for all hooks handler"""
    debug_logger = get_debug_logger()

    try:
        # イベントデータを読み込み
        event = load_hook_event(sys.stdin)

        debug_logger.info(f"Processing hook event: {event.hook_event_name}")

        # ディスパッチャーで適切なハンドラーに振り分け
        dispatcher = EventDispatcher()
        dispatcher.dispatch(event)

        # 元のイベントデータを出力（透過性を保つ）
        write_hook_event(event, sys.stdout)

    except json.JSONDecodeError as e:
        debug_logger.error(f"Invalid JSON input: {e}")
        # エラーでも空のJSONを出力して処理を続行
        print(json.dumps({}))
        sys.exit(1)

    except Exception as e:
        debug_logger.error(f"Unexpected error in hook handler: {e}", exc_info=True)
        # エラーでも元のデータを出力して処理を続行
        try:
            # 可能な限り元のデータを出力
            if "event" in locals():
                write_hook_event(event, sys.stdout)
            else:
                print(json.dumps({}))
        except Exception:
            print(json.dumps({}))
        sys.exit(1)


if __name__ == "__main__":
    main()
