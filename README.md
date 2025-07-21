# My personal Claude Code Hook Handlers

[![test](https://github.com/yuya-takeyama/cchh/actions/workflows/test.yaml/badge.svg)](https://github.com/yuya-takeyama/cchh/actions/workflows/test.yaml)

My personal Claude Code hook handlers for Slack notifications and voice feedback.

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
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL_ID="C0123456789"
```

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
```

## License

MIT