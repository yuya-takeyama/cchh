"""Main entry point for hook handler"""

import json
import os
import sys

from .handlers import HookHandler
from .logger import error_logger, hook_logger, logger
from .utils import get_session_id


def main() -> None:
    """Main entry point for hook handler"""
    try:
        # Read JSON from stdin
        input_data = json.loads(sys.stdin.read())

        # Get hook type from environment or input
        hook_type = input_data.get("hook_event_name", "Unknown")

        # Get session ID from hook data
        session_id = get_session_id(input_data)

        # Get cwd from hook data (フォールバックとして現在のディレクトリを使用)
        cwd = input_data.get("cwd", os.getcwd())

        # Log the event
        hook_logger.log_event(hook_type, input_data, session_id)

        # Create handler
        handler = HookHandler(session_id, cwd)

        # Check for new session
        if handler.session_manager.is_new_session:
            handler.handle_session_start()

        # Handle specific hook types
        if hook_type == "PreToolUse":
            handler.handle_pre_tool_use(input_data)
        elif hook_type == "PostToolUse":
            handler.handle_post_tool_use(input_data)
        elif hook_type == "Notification":
            handler.handle_notification(input_data)
        elif hook_type == "Stop":
            handler.handle_stop(input_data)
        elif hook_type == "UserPromptSubmit":
            handler.handle_user_prompt_submit(input_data)

        # Output original data for transparency
        # Skip output for UserPromptSubmit when it's a new session to avoid duplicate cwd display
        if not (
            hook_type == "UserPromptSubmit" and handler.session_manager.is_new_session
        ):
            print(json.dumps(input_data))

    except Exception as e:
        logger.error(f"Hook handler error: {e}", exc_info=True)

        # Log to error file with context
        context = {
            "hook_type": hook_type if "hook_type" in locals() else "Unknown",
            "session_id": session_id if "session_id" in locals() else "Unknown",
            "cwd": cwd if "cwd" in locals() else os.getcwd(),
        }

        # Add input data if available (but limit size)
        if "input_data" in locals():
            context["input_data"] = input_data
            if len(json.dumps(input_data)) > 5000:
                context["input_data"] = {"note": "Input data too large, truncated"}

        error_logger.log_error(
            error_type="main_handler_error",
            error_message=str(e),
            context=context,
            exception=e,
        )

        # Still output the original data even if processing fails
        print(json.dumps(input_data if "input_data" in locals() else {}))
        sys.exit(1)


if __name__ == "__main__":
    main()
