# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Testing
```bash
# Run all tests with coverage
uv run task test

# Run specific test module
uv run pytest tests/slack/test_notifier.py -v

# Run specific test class
uv run pytest tests/core/test_dispatcher.py::TestEventDispatcher -v

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing
```

### Code Quality
```bash
# Run linting
uv run task lint

# Format code
uv run task format

# Type checking
uv run task typecheck

# Run all checks (lint + test + typecheck)
uv run task all
```

### Development Setup
```bash
# Install dependencies
uv sync

# Clean build artifacts
uv run task clean
```

## High-Level Architecture

CCHH (Claude Code Hook Handlers) is a modular Python application that handles Claude Code hook events and dispatches them to various notification systems.

### Event Flow
1. **Entry Point**: `all_hooks.py` receives JSON events from Claude Code via stdin
2. **Event Dispatcher**: `src/core/dispatcher.py` routes events to enabled handlers
3. **Handlers**: Three main handlers process events in parallel:
   - **Slack Notifier**: Sends notifications to Slack with thread-based session tracking
   - **Zunda Speaker**: Provides voice feedback using Zundamon text-to-speech
   - **Event Logger**: Logs all events to JSONL format for analysis

### Key Design Patterns
- **Plugin Architecture**: Each handler implements the `HookHandler` interface from `src/core/base.py`
- **Dependency Injection**: Handlers are initialized conditionally based on environment variables
- **Session Management**: Slack handler maintains session state in `~/.claude/slack_thread_ts/`
- **Error Isolation**: Each handler's errors are caught independently to prevent cascading failures

### Module Organization
- `src/core/`: Core types and event dispatching logic
- `src/slack/`: Slack integration with session tracking and message formatting
- `src/zunda/`: Voice notification system with command parsing
- `src/logger/`: JSONL event logging with rotation
- `src/utils/`: Shared utilities for I/O, parsing, and configuration

### Configuration
All features are controlled via environment variables:
- Slack: `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`, `SLACK_NOTIFICATIONS_ENABLED`
- Zunda: `ZUNDA_SPEAKER_ENABLED`, `ZUNDA_SPEAK_ON_PROMPT_SUBMIT`
- Logging: `EVENT_LOGGING_ENABLED`, `LOG_MAX_SIZE_MB`

### Special Files
- `ruff_hook.py`: Standalone hook for PostToolUse that runs Ruff formatter on Python files
- `event_logger.sh`: Simple shell script for basic event logging (legacy)
