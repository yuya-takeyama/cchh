# My personal Claude Code Hook Handlers

[![test](https://github.com/yuya-takeyama/cchh/actions/workflows/test.yaml/badge.svg)](https://github.com/yuya-takeyama/cchh/actions/workflows/test.yaml)

My personal Claude Code hook handlers for Slack notifications and voice feedback.

## Requirements

- Python 3.13+

## Features

- **Slack notifications**: Tool executions, errors, and session management
- **Voice feedback**: Important events via Zundamon TTS
- **Session tracking**: Thread-based Slack session management
- **Event logging**: JSONL format logging for analysis

## Setup

```bash
# Install dependencies
uv sync

# Configure environment variables
export CCHH_SLACK_BOT_TOKEN="xoxb-your-token"
export CCHH_SLACK_CHANNEL_ID="C0123456789"
```

## Environment Variables

### Slack Configuration
- `CCHH_SLACK_BOT_TOKEN`: Slack Bot Token (xoxb-...)
- `CCHH_SLACK_CHANNEL_ID`: Notification channel ID
- `CCHH_SLACK_NOTIFICATIONS_ENABLED`: Enable/disable Slack notifications (default: true)
- `CCHH_SLACK_SHOW_SESSION_START`: Show cwd on session start (default: true)
- `CCHH_SLACK_NOTIFY_ON_TOOL_USE`: Notify on tool usage (default: true)
- `CCHH_SLACK_NOTIFY_ON_STOP`: Notify on stop events (default: true)
- `CCHH_SLACK_COMMAND_MAX_LENGTH`: Max command display length (default: 200)

### Zunda Voice Configuration
- `CCHH_ZUNDA_SPEAKER_ENABLED`: Enable/disable voice feedback (default: true)

### Event Logging Configuration
- `CCHH_EVENT_LOGGING_ENABLED`: Enable/disable event logging (default: true)
- `CCHH_LOG_MAX_SIZE_MB`: Max log file size in MB (default: 100)
- `CCHH_LOG_ROTATION_COUNT`: Log rotation count (default: 5)

### Other
- `CCHH_TEST_ENVIRONMENT`: Test environment flag (disables notifications during tests)
- `CCHH_CLAUDE_SESSION_ID`: Claude session ID

## Claude Code Integration

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/cchh && uv run python all_hooks.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command", 
            "command": "cd /path/to/cchh && uv run python all_hooks.py"
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/cchh && uv run python ruff_hook.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/cchh && uv run python all_hooks.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/cchh && uv run python all_hooks.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/cchh && uv run python all_hooks.py"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/cchh && uv run python all_hooks.py"
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/cchh` with your actual path.

## Development

```bash
# Run tests
uv run task test

# Format and lint
uv run task format
uv run task lint

# Type checking
uv run task typecheck

# Run all checks (lint + test + typecheck)
uv run task all

# Clean build artifacts
uv run task clean
```

## License

MIT