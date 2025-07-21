#!/usr/bin/env python3
"""
Test runner for hook handler tests

This script runs all tests in the hook_handler.tests package using pytest.
"""

import subprocess
import sys

if __name__ == "__main__":
    # Run pytest with appropriate arguments
    cmd = [sys.executable, "-m", "pytest", "hook_handler/tests", "-v"]
    sys.exit(subprocess.call(cmd))
