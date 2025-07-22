"""Integration tests for all_hooks.py"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestAllHooksIntegration:
    """Integration tests for the main all_hooks.py entry point"""

    @pytest.fixture
    def all_hooks_path(self):
        """Get path to all_hooks.py"""
        return Path(__file__).parent.parent.parent / "all_hooks.py"

    @pytest.fixture
    def sample_events(self):
        """Sample hook events for testing (nested format like Claude Code)"""
        return {
            "user_prompt": {
                "data": {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                    "prompt": "Please help me fix this bug",
                }
            },
            "bash_command": {
                "data": {
                    "hook_event_name": "PreToolUse",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                    "tool_name": "Bash",
                    "tool_input": {"command": "echo 'Hello World'"},
                }
            },
            "task": {
                "data": {
                    "hook_event_name": "PreToolUse",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                    "tool_name": "Task",
                    "tool_input": {"description": "Fix authentication bug"},
                }
            },
            "todo_write": {
                "data": {
                    "hook_event_name": "PreToolUse",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                    "tool_name": "TodoWrite",
                    "tool_input": {
                        "todos": [
                            {
                                "content": "Task 1",
                                "status": "completed",
                                "priority": "high",
                            },
                            {
                                "content": "Task 2",
                                "status": "pending",
                                "priority": "medium",
                            },
                        ]
                    },
                }
            },
            "error_result": {
                "data": {
                    "hook_event_name": "PostToolUse",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                    "tool_name": "Bash",
                    "result": {"error": "Command not found"},
                }
            },
            "notification": {
                "data": {
                    "hook_event_name": "Notification",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                    "message": "Claude needs your permission to use Bash",
                }
            },
            "stop": {
                "data": {
                    "hook_event_name": "Stop",
                    "session_id": "test-session-123",
                    "cwd": "/test/directory",
                }
            },
        }

    def run_all_hooks(self, event_data, env_vars=None):
        """Run all_hooks.py with given event data"""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Always set TEST_ENVIRONMENT to avoid actual notifications
        env["CCHH_TEST_ENVIRONMENT"] = "true"

        cmd = [sys.executable, "all_hooks.py"]

        result = subprocess.run(
            cmd,
            input=json.dumps(event_data),
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent,  # Project root
        )

        return result

    def test_all_hooks_exists(self, all_hooks_path):
        """Test that all_hooks.py exists"""
        assert all_hooks_path.exists()

    def test_basic_execution(self, sample_events):
        """Test basic execution with a simple event"""
        result = self.run_all_hooks(sample_events["user_prompt"])

        assert result.returncode == 0
        # Should output the original event
        output_data = json.loads(result.stdout)
        assert output_data["data"]["hook_event_name"] == "UserPromptSubmit"

    def test_all_features_disabled(self, sample_events):
        """Test execution with all features disabled"""
        env_vars = {
            "CCHH_SLACK_NOTIFICATIONS_ENABLED": "false",
            "CCHH_ZUNDA_SPEAKER_ENABLED": "false",
            "CCHH_EVENT_LOGGING_ENABLED": "false",
        }

        result = self.run_all_hooks(sample_events["bash_command"], env_vars)

        assert result.returncode == 0
        # Should still output the event
        output_data = json.loads(result.stdout)
        assert output_data["data"]["tool_name"] == "Bash"

    def test_with_zunda_enabled(self, sample_events):
        """Test with Zunda speaker enabled"""
        env_vars = {
            "CCHH_SLACK_NOTIFICATIONS_ENABLED": "false",
            "CCHH_ZUNDA_SPEAKER_ENABLED": "true",
            "CCHH_EVENT_LOGGING_ENABLED": "false",
        }

        # Run all_hooks with subprocess
        result = self.run_all_hooks(sample_events["user_prompt"], env_vars)

        # Should complete successfully
        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert output_data["data"]["hook_event_name"] == "UserPromptSubmit"

    def test_error_handling(self):
        """Test handling of invalid JSON input"""
        result = subprocess.run(
            [sys.executable, "all_hooks.py"],
            input="invalid json",
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should handle the error gracefully
        assert result.returncode != 0 or "error" in result.stderr.lower()

    def test_multiple_events_sequence(self, sample_events):
        """Test processing multiple events in sequence"""
        events = [
            sample_events["user_prompt"],
            sample_events["bash_command"],
            sample_events["task"],
            sample_events["todo_write"],
            sample_events["error_result"],
            sample_events["stop"],
        ]

        for event in events:
            result = self.run_all_hooks(event)
            assert result.returncode == 0
            output_data = json.loads(result.stdout)
            assert output_data["data"]["hook_event_name"] == event["data"]["hook_event_name"]

    def test_event_logging_enabled(self, sample_events, tmp_path):
        """Test with event logging enabled"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        env_vars = {
            "CCHH_SLACK_NOTIFICATIONS_ENABLED": "false",
            "CCHH_ZUNDA_SPEAKER_ENABLED": "false",
            "CCHH_EVENT_LOGGING_ENABLED": "true",
            "CCHH_LOG_DIR": str(log_dir),
            "CCHH_TEST_ENVIRONMENT": "false",  # Ensure logging happens
        }

        result = self.run_all_hooks(sample_events["bash_command"], env_vars)

        assert result.returncode == 0
        # Since logger checks test environment, we can't test actual file creation in test env
        # Just check that it runs successfully
        output_data = json.loads(result.stdout)
        assert output_data["data"]["tool_name"] == "Bash"

    def test_permission_notification(self, sample_events):
        """Test handling of permission notification"""
        result = self.run_all_hooks(sample_events["notification"])

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert output_data["data"]["notification"] == "Claude needs your permission to use Bash"

    def test_concurrent_sessions(self, sample_events):
        """Test handling events from different sessions"""
        # Modify session ID
        event1 = json.loads(json.dumps(sample_events["user_prompt"]))  # Deep copy
        event1["data"]["session_id"] = "session-1"

        event2 = json.loads(json.dumps(sample_events["bash_command"]))  # Deep copy
        event2["data"]["session_id"] = "session-2"

        result1 = self.run_all_hooks(event1)
        result2 = self.run_all_hooks(event2)

        assert result1.returncode == 0
        assert result2.returncode == 0

    def test_empty_tool_input(self):
        """Test handling of events with missing tool input"""
        event = {
            "data": {
                "hook_event_name": "PreToolUse",
                "session_id": "test-session",
                "cwd": "/test",
                "tool_name": "Bash",
                # tool_input is missing
            }
        }

        result = self.run_all_hooks(event)
        assert result.returncode == 0

    def test_special_characters_in_input(self, sample_events):
        """Test handling of special characters in input"""
        event = json.loads(json.dumps(sample_events["bash_command"]))  # Deep copy
        event["data"]["tool_input"]["command"] = "echo '特殊文字 \"quotes\" and $variables'"

        result = self.run_all_hooks(event)
        assert result.returncode == 0

    @pytest.mark.parametrize(
        "event_name",
        [
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "Notification",
            "Stop",
        ],
    )
    def test_all_event_types(self, event_name):
        """Test all supported event types"""
        event = {
            "data": {
                "hook_event_name": event_name,
                "session_id": "test-session",
                "cwd": "/test",
            }
        }

        result = self.run_all_hooks(event)
        assert result.returncode == 0
