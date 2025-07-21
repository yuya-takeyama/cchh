# CCHH Developer Guide

## Overview

Hook handler system for Claude CLI that captures various CLI events (pre/post tool execution, notifications, session start/stop) and executes custom processing like Slack notifications and voice feedback.

## Tech Stack

- **Language**: Python 3.13+
- **Package Manager**: uv
- **Task Runner**: taskipy (npm scripts-like experience)
- **Formatter**: ruff
- **Testing**: pytest + pytest-cov
- **CI/CD**: GitHub Actions

## Project Structure

```
cchh/
├── pyproject.toml           # Python project config (uv + taskipy + ruff)
├── README.md               # User documentation
├── DEVELOPER.md            # This file - developer documentation
├── LICENSE                 # MIT License
├── uv.lock                # Dependency lock file
├── all_hooks.py           # Main entry point
├── ruff_hook.py           # Ruff formatter hook
├── src/                   # Main package
│   ├── __init__.py
│   ├── core/               # Core functionality
│   │   ├── dispatcher.py   # Event dispatcher
│   │   └── types.py        # Type definitions
│   ├── slack/              # Slack notification
│   │   ├── notifier.py     # Slack notifier
│   │   └── session_tracker.py # Session management
│   ├── zunda/              # Zunda voice
│   │   ├── speaker.py      # Voice speaker
│   │   └── command_formatter.py # Command formatting
│   ├── logger/             # Event logging
│   │   └── event_logger.py # JSONL logger
│   └── utils/              # Utilities
│       ├── command_parser.py # Command parsing
│       ├── io_helpers.py   # I/O helpers
│       └── logger.py       # Debug logger
├── tests/                  # Unit tests
│   ├── core/
│   ├── slack/
│   ├── zunda/
│   ├── logger/
│   └── integration/
├── test_*.py               # Helper test scripts
├── event_logger.sh         # Event logging script
├── aqua/                   # Tool management with aqua
└── .github/
    └── workflows/
        └── test.yaml       # CI configuration
```

## Core Features

### 1. Hook Event Processing

- **PreToolUse**: Pre-tool execution processing
- **PostToolUse**: Post-tool execution processing
- **Notification**: Claude notifications
- **Stop**: Session termination
- **UserPromptSubmit**: User prompt submission

### 2. Notification System

- **Slack notifications**: Important commands/tasks to Slack
- **Voice feedback**: Audio guidance via Zundamon
- **Logging**: Event logging (hooks.log)

### 3. Session Management

- Session ID-based state management
- New session detection and initialization
- Working directory tracking

## Development Commands

### Available Tasks (via taskipy)

All commands use `uv run task <command>` format:

| Command                 | Description                   | Actual Command                             |
| ----------------------- | ----------------------------- | ------------------------------------------ |
| `uv run task dev`       | Setup development environment | `uv sync`                                  |
| `uv run task test`      | Run tests with coverage       | `pytest`                                   |
| `uv run task lint`      | Lint code with ruff           | `ruff check .`                             |
| `uv run task format`    | Format code with ruff         | `ruff format .`                            |
| `uv run task typecheck` | Type checking with mypy       | `mypy src`                                 |
| `uv run task all`       | Run all checks                | `task lint && task test && task typecheck` |
| `uv run task clean`     | Clean build artifacts         | Complex cleanup script\*                   |

\*Clean command removes:

- Virtual environment (.venv/)
- Python cache files (**pycache**/, \*.pyc)
- Test artifacts (.coverage, .pytest_cache/)
- Ruff cache (.ruff_cache/)

### Direct uv Commands

```bash
# Alternative to task commands
uv sync                    # Install dependencies
uv run pytest             # Run tests directly
uv run ruff check .       # Lint directly
uv run ruff format .      # Format directly
uv run mypy src          # Type check directly
```

## Code Quality Configuration

### Ruff Settings (pyproject.toml)

- **Target**: Python 3.13
- **Line length**: 88 characters
- **Rules**: pycodestyle, pyflakes, isort, flake8-bugbear, pyupgrade
- **Format**: Double quotes, space indentation

### Test Configuration

- **Test path**: `tests`
- **Coverage**: term-missing reports
- **Branch coverage**: Enabled
- **Test files**: `test_*.py` pattern
- **Coverage threshold**: Aim for >85%

## Claude CLI Integration

### Hook Configuration

Example settings.json configuration:

```json
{
  "hooks": {
    "preToolUse": "python /path/to/cchh/all_hooks.py",
    "postToolUse": "python /path/to/cchh/all_hooks.py",
    "notification": "python /path/to/cchh/all_hooks.py",
    "stop": "python /path/to/cchh/all_hooks.py",
    "userPromptSubmit": "python /path/to/cchh/all_hooks.py"
  }
}
```

### Environment Variables

- `SLACK_BOT_TOKEN`: Slack Bot Token (xoxb-...)
- `SLACK_CHANNEL_ID`: Channel ID for notifications
- `SLACK_ENABLED`: Enable/disable Slack (default: 1)
- `TEST_ENVIRONMENT`: Test flag (disables external notifications)

## Architecture Notes

### Modular Design

The project follows a modular architecture:

1. **core/dispatcher.py**: Central event routing
2. **slack/notifier.py**: Slack notification interface
3. **zunda/speaker.py**: Voice notification interface
4. **logger/event_logger.py**: Structured logging with JSONL format
5. **utils/**: Shared utilities and helpers
6. ***/config.py**: Module-specific configuration

### Testing Strategy

- Unit tests for each module
- Mock external dependencies (Slack API, filesystem)
- Test coverage >85%
- Type checking with mypy

### Performance Considerations

- Async notifications to avoid blocking CLI
- Efficient session state caching
- Log rotation for high-volume usage

## Contributing

### Development Workflow

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run `uv run task all` to ensure quality
5. Commit with conventional commits
6. Push and create a pull request

### Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and testable

### Testing Guidelines

- Write tests for new features
- Maintain test coverage >85%
- Use descriptive test names
- Mock external dependencies

## Debugging Tips

### Log Files

- **~/.claude/hooks.log**: All hook events in JSONL format
- **~/.claude/cchh_errors.log**: Error logs
- **~/.claude/slack_thread_ts/**: Session state files

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes the project root
2. **Slack not working**: Check SLACK_BOT_TOKEN and SLACK_CHANNEL_ID
3. **Tests failing**: Run `uv sync` to update dependencies

### Debug Mode

Set `TEST_ENVIRONMENT=1` to disable external notifications during development.

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG (if exists)
3. Create a git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions will run tests automatically

## Future Improvements

- [ ] Add more hook event types support
- [ ] Implement plugin system for custom handlers
- [ ] Add configuration file support
- [ ] Improve error recovery mechanisms
- [ ] Add metrics and monitoring
